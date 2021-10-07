#include "pins_arduino.h"
#include <avr/pgmspace.h>
#include <math.h>
#include <stdint.h>

#include "Uno9341TFT.h"
#include "terminal_constants.h"
#include "ansicodes.h"
#include "myfont.h"

//#define BAUDRATE (1200)
//#define BAUDRATE (2400)
//#define BAUDRATE (4800)
//#define BAUDRATE (9600)
//#define BAUDRATE (19200)
//#define BAUDRATE (38400)
#define BAUDRATE (57600)
//#define BAUDRATE (115200)

// Clip an integer to a range of values
#define CLIP(x,lo,hi) (min(hi,max(lo,(x))))

////////////////////////////////////////////////////////////////////////////////
// Global state

// The LCD screen
Uno9341TFT tft;

// State for virtual terminal.
byte row = TR-1;
byte col = 0;

// Registers for stashing cursor state
byte saved_row = TR-1;
byte saved_col = 0;

// Color registers: foreground, background, underline
byte fg = (byte)FG_DEFAULT;
byte bg = (byte)BG_DEFAULT;
byte ul = (byte)FG_DEFAULT;

// Font effects registers
byte invert         = NORMAL;
byte font_weight    = NORMAL;
byte font_mode      = NORMAL;
byte blink_mode     = NORMAL;
byte underline_mode = NORMAL;
byte overline_mode  = NORMAL;
byte strike_mode    = NORMAL;
byte frame_mode     = NORMAL;
byte script_mode    = NORMAL;

// Cursor drawing is very brittle, since we need to draw/erase with xor
byte cursor_visible = 1;

// To emulate the bell, we invert the screen for a time.
volatile unsigned int bell_counter = 0;

// Blink loop in the background
// We store information needed for the blink code in a bit-vector
// To avoid slowing down scrolling, we pad each row to a whole number of bytes
// Blink flags are set in the advance_cursor function in terminal_misc.h

#define BLINK_BYTES_PER_ROW (TC/8+1)
#define BLINK_BYTES         (TR*BLINK_BYTES_PER_ROW)

// Routines to get/set/clear the blink bitvector
#define BVEC_GET(bitvector,  row, column) ((bitvector[row*BLINK_BYTES_PER_ROW + ((column)>>3)]>> ((column)&0b111))&1)
#define BVEC_SET(bitvector,  row, column)  (bitvector[row*BLINK_BYTES_PER_ROW + ((column)>>3)]|= (1<<((column)&0b111)))
#define BVEC_CLEAR(bitvector,row, column)  (bitvector[row*BLINK_BYTES_PER_ROW + ((column)>>3)]&=~(1<<((column)&0b111)))

volatile byte blinking[BLINK_BYTES];
volatile byte highlight[BLINK_BYTES];
// Variables for the blink-rendering state machine
#define BLINK_DELAY (15000)
volatile unsigned long blink_counter=0;
volatile unsigned int  blink_r=0;
volatile unsigned int  blink_c=0;
volatile byte blinkphase=0;

// Global buffer used for copying data
byte copy_buffer[256];

// Persistent state: a memory of the current or most recent character bitmap
// One byte per row
byte char_bitmap[CH]; 

// We need to keep track of whether the current position contains a valid
// character bitmap that is allowed to combine with combining modifiers.
// This flag is set after a character bitmap is drawn.
byte combining_ok = 0;
byte new_combining_ok = 0;
byte prev_row = 0;
byte prev_col = 0;

////////////////////////////////////////////////////////////////////////////////
// Code organized into different header files. This is *slightly* abusing header
// files. Please include these files here and ONLY here, in this order.
#include "textgraphics.h"
#include "terminal_misc.h"
#include "fontmap.h"
#include "unicode.h"
#include "control.h"


////////////////////////////////////////////////////////////////////////////////
// for hosts that support XON/XOFF flow control
// Add the ixon with stty when configuring the serial port
// These have been removed, they just seemed to mess things up
/*
void pause_incoming_serial() {
  Serial.write(XOFF); 
  Serial.flush();
}
void resume_incoming_serial() {
  Serial.write(XON); 
  Serial.flush();
}
*/

////////////////////////////////////////////////////////////////////////////////
// setup and loop 

void setup(void) 
{
  tft.begin();
  reset();
  Serial.begin(BAUDRATE);
  // Software control flow: Let the host know that we are NOT ready until we 
  // say so! (It is very likely that this simply doesn't work on Linux)
  //pause_incoming_serial();
  // Drain the buffer so we know we're starting from a clean slate.
  while (Serial.available()) Serial.read();
  // Again, these may do nothing
  //resume_incoming_serial();
}

/** Run animation/blink routines in the background, while idle 
 */
void idle() {
  // "Bell" implemented as full-screen blink
  if (bell_counter>0) { bell_counter--; return; }
  COMMAND(ILI9341_INVERTOFF);
  
  // "Blink machine"
  if (blink_counter) {blink_counter--; return;}
  blink_c++;
  if (blink_c>=TC) {
    // End of row. Continue to next row. 
    blink_c=0; blink_r++;
    // End of screen. Start again at beginning. Toggle the blink phase bit. 
    if (blink_r>=TR) {blink_r=0; blinkphase^=1; blink_counter=BLINK_DELAY;}
  }
  // Check if location is blinking, and whether it is highlighted
  byte isblinking  = BVEC_GET(blinking ,blink_r,blink_c);
  byte ishighlight = BVEC_GET(highlight,blink_r,blink_c);
  // Change highlight to correct state 
  if ((blinkphase || !isblinking) && ishighlight) {
    invert_location(blink_r,blink_c); 
    BVEC_CLEAR(highlight,blink_r,blink_c);
  } else if (isblinking  && !blinkphase && !ishighlight) {
    invert_location(blink_r,blink_c); 
    BVEC_SET(highlight,blink_r,blink_c);
  }
}

volatile byte keepalive_counter = 0;

void loop(void) {
  while (Serial.available()) {
    // Process next byte of input.
    byte inByte = (byte)(Serial.read());
    // If the input results in a caharacter that can 
    // accept combining marks, this flag will be set. 
    new_combining_ok = 0;
    if (inByte<32) switch (inByte) {
      case BELL: bell(); break;
      case BACKSPACE: backspace(); break;  
      case HORIZONTAL_TAB: {
        byte colto = min(TC-1,(col+5)&0b11111100);
        byte spaces = colto-col;
        for (byte i=0; i<spaces; i++) print(" "); 
        } break;     
      case NEWLINE:       
        cstamp(); 
        newline(); 
        cstamp(); 
        break;
      case VERTICAL_TAB:    
        cstamp(); 
        scroll(max(0,4-row)); 
        row=max(0,row-4); 
        cstamp(); 
        break;
      case FORM_FEED:       
        cstamp(); 
        scroll(max(0,1-row)); 
        row=max(0,row-1); 
        cstamp(); 
        break;
      case CARRIAGE_RETURN: 
        cstamp(); 
        col=0;     
        cstamp();
        break;
      case ESCAPE: 
        switch (blocking_read()) {
          case '[': parse_CSI_sequence(); break; // CSI sequence
          case '7': save_cursor();        break; // Save cursor            
          case '8': restore_cursor();     break; // Restore cursor
          case 'c': reset();              break; // Reset all state
        }
        break;
    } else if (inByte<0x7E) {
      // Fast-track ASCII
      prepare_cursor();
      _basiclatin((byte)inByte);
      drawStyledChar();
      advance_cursor(1);       
    } else if (inByte<0xA0) switch (inByte) {
      // High control code? 
      case DELETE: backspace();          break;
      case CSI:    parse_CSI_sequence(); break;
    } else if (inByte>=0b11000000) {
      // UTF-8, Parse as unicode
      if (parse_utf8(inByte)==FAIL) {
        // We should know if something bad happened
        prepare_cursor();
        load_glyph_bitmap(REPLACEMENT_CHARACTER);
        drawCharFancy(CH*row,CW*col,RED,BLACK,NORMAL,NORMAL,HALFWIDTH);
        advance_cursor(1);
      }
    }
    // Update whether the most recently drawn character should accept
    // combining modifiers
    combining_ok = new_combining_ok;
  } 
  idle();
}

// rrrrrggg gggbbbbb
// rrrbbggg rrrbbggg


