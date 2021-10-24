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
#include "blinker.h"
#include "textgraphics.h"
#include "terminal_misc.h"
#include "fontmap.h"
#include "control.h"

////////////////////////////////////////////////////////////////////////////////
// setup and loop 

void setup(void) 
{
  tft.begin();
  reset();
  Serial.begin(BAUDRATE);
  
  /*
  // Test 1: just say hello over serial
  Serial.println("Hello");
  
  // Test 2: check that basic graphics drivers work
  tft.fillScreen(RED);
  tft.fillScreen(GREEN);
  tft.invertRect(240/4,320/4,240/2,320/2);
  
  // Test 3: Can we load and draw glyph bitmaps? 
  row = TR-1;
  col = 0;
  unsigned long time0 = millis();
  hide_cursor();
  for (unsigned int i=0; i<NGLYPHS; i++) {
    prepare_cursor();
    load_glyph_bitmap(i);
    drawStyledChar();
    advance_cursor(1);
  }
  unsigned long time1 = millis();
  Serial.print("Time took was: ");
  Serial.println(time1-time0);
  */
  
  // Test 4: does unicode mapping work? 
  /*
  reset();
  hide_cursor();
  for (unsigned long i=0; i<=100000; i++) {
  //for (unsigned long i=0x900; i<=0x97F; i++) {
  //for (unsigned long i=0x1F; i<=0x7E; i++) {
  //char i = '>';//>\}
    // byte blockinfo = find_unicode_debug(i);
    // Serial.print(i);
    // Serial.print(": ");
    // Serial.println(blockinfo);
    // For ascii returns 82
    // That's index 20 and code 2
    // For a dense block. DENSE=2
    // Index 20 indeed matches basic latin
    // bstart 756 ? First offset 32? This checks out
    // Codes look find; Code definitions broken?
    // Code definitions look fine, dig deeper. 
    // Can we get what code is retrieved and how it is interpreted? 
    prepare_cursor();
    byte return_code = load_unicode(i);
    
    if (return_code == LOADED) {
      // Soft-fonts draw, but mapped fonts only load the character bitmap.
      // This allows the mathematical alphanumerics soft-font to re-use the
      // unicode mapping for Greek, without drawing to screen, in order to
      // further style characters before drawing. 
      drawStyledChar();
      advance_cursor(1);   
      //resume_incoming_serial();
    }
    else if (return_code != SUCCESS) {//and return_code != NOT_MAPPED) {
      //load_and_draw_glyph(REPLACEMENT_CHARACTER);
      load_glyph_bitmap(REPLACEMENT_CHARACTER);
      drawCharFancy(CH*row,CW*col,fg,bg,NORMAL,NORMAL,HALFWIDTH);
      advance_cursor(1);
    }
  
    //drawStyledChar();
    //advance_cursor(1);
    if (i%(TR*TC)==TR*TC-1) { delay(1000); reset(); }
  }
  while (1);
  */
}

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
      case DEVICE_CONTROL4:
        // Non-standard code; Using this for screen capture; 
        // Experimental! 
        {
          bell();
          for (int y=0; y<320; y++) {
            SET_XY_RANGE(0,239,y);
            tft.readPixels(240, copy_buffer);
            for (byte x=0; x<240; x++) { 
              Serial.write(copy_buffer[240-1-x]);
            }
          }
        }
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
      // Fast-track ASCII TODO
      if (parse_utf8(inByte)==FAIL) {
        // We should know if something bad happened
        prepare_cursor();
        load_glyph_bitmap(REPLACEMENT_CHARACTER);
        drawCharFancy(CH*row,CW*col,YELLOW,BLACK,NORMAL,NORMAL,HALFWIDTH);
        advance_cursor(1);
      }
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
        drawCharFancy(CH*row,CW*col,BLUE,BLACK,NORMAL,NORMAL,HALFWIDTH);
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


