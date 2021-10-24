#ifndef BLINKER_H
#define BLINKER_H

// To emulate the bell, we invert the screen for a time.
volatile unsigned int bell_counter = 0;

// Blink loop in the background
// We store information needed for the blink code in a bit-vector
// To avoid slowing down scrolling, we pad each row to a whole number of bytes
// Blink flags are set in the advance_cursor function in terminal_misc.h

#define BLINK_BYTES_PER_ROW (TC/8+1)
#define BLINK_BYTES         (TR*BLINK_BYTES_PER_ROW)

// Routines to get/set/clear the blink bitvector
// These require an alarming amount of space, let's make them functions
// instead?
//#define BVEC_GET(bitvector,  row, column) ((bitvector[row*BLINK_BYTES_PER_ROW + ((column)>>3)]>> ((column)&0b111))&1)
//#define BVEC_SET(bitvector,  row, column)  (bitvector[row*BLINK_BYTES_PER_ROW + ((column)>>3)]|= (1<<((column)&0b111)))
//#define BVEC_CLEAR(bitvector,row, column)  (bitvector[row*BLINK_BYTES_PER_ROW + ((column)>>3)]&=~(1<<((column)&0b111)))

byte BVEC_GET(volatile byte *bitvector,  byte row, byte column) {
  return (bitvector[row*BLINK_BYTES_PER_ROW + ((column)>>3)]>> ((column)&0b111))&1;
}
void BVEC_SET(volatile byte *bitvector,  byte row, byte column) {
  bitvector[row*BLINK_BYTES_PER_ROW + ((column)>>3)]|= (1<<((column)&0b111));
}
void BVEC_CLEAR(volatile byte *bitvector,byte row, byte column) {
  bitvector[row*BLINK_BYTES_PER_ROW + ((column)>>3)]&=~(1<<((column)&0b111));
}

volatile byte blinking[BLINK_BYTES];
volatile byte highlight[BLINK_BYTES];
// Variables for the blink-rendering state machine
#define BLINK_DELAY (15000)
volatile unsigned long blink_counter=0;
volatile unsigned int  blink_r=0;
volatile unsigned int  blink_c=0;
volatile byte blinkphase=0;


void mark_cleared_for_blink(unsigned int start_index_inclusive, unsigned int end_index_exclusive) {
  unsigned int i = start_index_inclusive;
  // TODO OPTIMIZE THIS
   while (i<end_index_exclusive) {
     unsigned int c = i%TC;
     unsigned int r = i/TC;
     byte byte_index = r*BLINK_BYTES_PER_ROW + (c>>3);
     byte bit_mask   = ~(1<<(c&0b111));
     blinking [byte_index] &= bit_mask;
     highlight[byte_index] &= bit_mask;
     //BVEC_CLEAR(blinking,r,c);
     //BVEC_CLEAR(highlight,r,c);
     i++; 
   }
  /*
  while (i<end_index_exclusive && (i&0b111)) {
    BVEC_CLEAR(blinking,i);
    BVEC_CLEAR(highlight,i);
    i++;
  }
  byte j = i>>3;
  while (i+8<end_index_exclusive) {
    highlight[j] = blinking[j] = 0;
    i+=8; 
    j++;
  }
  while (i<end_index_exclusive) {
    BVEC_CLEAR(blinking,i);
    BVEC_CLEAR(highlight,i);
    i++;
  }*/
}

/** Reset blink state and blink machine state */
void clear_blink() {
  for (int i=0; i<BLINK_BYTES; i++) highlight[i]=blinking[i]=0;
  blink_r = blink_c = blink_counter = blinkphase = 0;
}

/** Scroll the blink/highlight buffers */
void scrollblink(int scroll_rows) {
  if (scroll_rows==0) return; 
  byte to,from,inc;
  if (scroll_rows>0) { // Scroll up: 
    to   = BLINK_BYTES-1;
    from = to - scroll_rows*BLINK_BYTES_PER_ROW;
    inc  = -1;
  }
  else { // Scroll down: 
    scroll_rows = -scroll_rows;
    to   = 0;
    from = scroll_rows*BLINK_BYTES_PER_ROW;
    inc  = 1;
  }
  for (byte i=scroll_rows; i<TR; i++) {
    for (byte j=0; j<BLINK_BYTES_PER_ROW; j++) {
      blinking [to] = blinking [from];
      highlight[to] = highlight[from];
      to+=inc; from+=inc;
    }
  }
}

/** Update the blink flag information. The "blink machine" needs this
 *  to render blinking text correctly
 */ 
inline void update_blink(byte r, byte c) {
  // Update "blink" flag for this location in the "blinking" bitvector
  byte byte_index = r*BLINK_BYTES_PER_ROW + (c>>3);
  byte bit_mask   = ~(1<<(c&0b111));
  highlight[byte_index] &= bit_mask;
  if (blink_mode==NORMAL) blinking[byte_index] &=  bit_mask;
  else                    blinking[byte_index] |= ~bit_mask;
}


// This weirdness a consequence of our abuse of header files
void invert_location(byte row, byte col);


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


#endif //BLINKER_H
