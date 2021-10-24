#ifndef TERMINAL_MISC_H
#define TERMINAL_MISC_H

#include "myfont.h"

////////////////////////////////////////////////////////////////////////////////
// Bulk drawing subroutines

/** Read `length` pixels then dump them to the screen, color inverted.
 *  optimized for speed: this assumes you have set the x and y limits
 *  to a tight box (x0,x1,y0,y1), so that the pixel location wraps 
 *  around to the beginning after we finish reading. This processes
 *  up to 256 pixels at a time.
 *  @param limit: length of pixels to invert
 */
void invert_flood(byte length) {
  // Adjust to move last read loop iteration out of the loop 
  // (optimization for speed, saves a couple instructions)
  length--;
  // Read pixels
  COMMAND(BEGIN_READ_DATA);
  READY_READ; SEND_DATA;
  setReadDir();
  READY_READ;
  DELAY1;
  byte i=0;
  for (;i<length;i++){ // Loop increment i++ acts as a DELAY (mandatory)
    byte b= READ_BYTE; // Read low byte of pixel data
    SEND_DATA;         // Discard the second byte
    READY_READ;        // (use hi_byte=lo_byte for 8-bit RRGGGBB)
    SEND_DATA;         // Advance to next pixel location
    copy_buffer[i]=b;  // Assign to buffer here to add DELAY (mandatory)
    READY_READ;        // Prepare to read next pixel
  }
  // Grab last byte as a special case
  copy_buffer[i]=READ_BYTE;
  setWriteDir();
  // Since we defined a tight box, position wraps around
  // Write inverted pixels
  COMMAND(BEGIN_PIXEL_DATA);
  for (i=0; i<=length; i++) {WRITE_BUS(~copy_buffer[i]); CLOCK_1;}
}

/** Invert coor bits for a single character */
void invert_location(byte row, byte col) {
  byte         x0 = row*CH;      // Bottom edge, in pixels
  byte         x1 = x0 + CH - 1; // Top edge
  unsigned int y0 = col*CW;      // Left edge
  unsigned int y1 = y0 + CW - 1; // Right edge
  SET_Y_RANGE(y0,y1); 
  SET_X_RANGE(x0,x1); 
  invert_flood(CH*CW);
  RESET_Y_RANGE();
}

void mark_cleared_for_blink(unsigned int start_index_inclusive, unsigned int end_index_exclusive) {
  unsigned int i = start_index_inclusive;
  // TODO OPTIMIZE THIS
   while (i<end_index_exclusive) {
     unsigned int c = i%TC;
     unsigned int r = i/TC;
     BVEC_CLEAR(blinking,r,c);
     BVEC_CLEAR(highlight,r,c);
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

/** Clear columns to the left of the current column on the current row */
void clear_left() {
  if (!col) return;
  tft.fillRect(row*CH,0,CH,col*CW,bg);
  mark_cleared_for_blink(row*TC,row*TC+col);
}

/** Clear current column and columns to the right on the current row */
void clear_right() {
  if (col*CW<SW) tft.fillRect(row*CH,col*CW,CH,SW-col*CW,bg);
  mark_cleared_for_blink(row*TC+col,row*TC+TC);
}

/** Clear rows above the current one */
void clear_above() {
  if (row>=TR-1) return;
  tft.fillRect((row+1)*CH,0,(TR-1-row)*CH,SW,bg);
  mark_cleared_for_blink((row+1)*TC,TC*TR);
}

/** Clear rows below the current one */
void clear_below() {
  if (!row) return;
  tft.fillRect(0,0,row*CH,SW,bg);
  mark_cleared_for_blink(0,row*TC);
}

/** Clear current line */ 
void clear_line() {
  tft.fillRect(row*CH,0,CH,SW,bg);
  mark_cleared_for_blink(row*TC,row*TC+TC);
}

/** Reset blink state and blink machine state */
void clear_blink() {
  for (int i=0; i<BLINK_BYTES; i++) highlight[i]=blinking[i]=0;
  blink_r = blink_c = blink_counter = blinkphase = 0;
}

/** Clear screen */
void clear_screen() {
  clear_blink(); 
  tft.fillScreen(bg);
}

/** Clear screen and reset cursor */
void reset_screen() {
  clear_screen(); 
  row=TR-1; 
  col=0;
}

/** Scroll the blink/highlight buffers */
void scrollblink(int scroll_rows) {
  if (scroll_rows==0) return; 
  // Scroll up: 
  if (scroll_rows>0) {
    byte to   = BLINK_BYTES-1;
    byte from = to - scroll_rows*BLINK_BYTES_PER_ROW;
    for (byte i=scroll_rows; i<TR; i++) {
      // (compiler might unroll this loop; try -O3 for speed)
      for (byte j=0; j<BLINK_BYTES_PER_ROW; j++) {
        blinking [to] = blinking [from];
        highlight[to] = highlight[from];
        to--; from--;
      }
    }
  }
  // Scroll down: 
  else {
    scroll_rows = -scroll_rows;
    byte to   = 0;
    byte from = scroll_rows*BLINK_BYTES_PER_ROW;
    for (byte i=scroll_rows; i<TR; i++) {
      for (byte j=0; j<BLINK_BYTES_PER_ROW; j++) {
        blinking [to] = blinking [from];
        highlight[to] = highlight[from];
        to++; from++;
      }
    }
  }
  
}

/** Scrolling is slow! */
void scroll(int scroll_rows) {
  if (!scroll_rows) return;
  scrollblink(scroll_rows);
  if (scroll_rows>=TR || scroll_rows<=-TR) {reset_screen(); return;}
  // Number of rows we'll need to copy
  byte readrows   = (TR-abs(scroll_rows));
  int  readpixels = readrows*CH;
  // Read columns one by one into this buffer
  boolean up = scroll_rows>0;
  uint8_t read_start  = up ? 0                : -scroll_rows*CH;
  uint8_t read_stop   = up ? readpixels       : SH-1;
  uint8_t write_start = up ? CH*scroll_rows   : 0;
  uint8_t write_stop  = SH-1;
  uint8_t clear_start = up ? 0                : readpixels;
  uint8_t clear_stop  = up ? scroll_rows*CH-1 : SH-1;
  for (unsigned int col=0; col<SW; col++) 
  { 
    SET_XY_RANGE(read_start,read_stop,col);
    tft.readPixels(readpixels, copy_buffer);
    SET_X_RANGE(write_start,write_stop);
    COMMAND(BEGIN_PIXEL_DATA);
    byte i=0;
    for (byte row=0; row<readrows; row++) { 
        // Compiler might unroll this loop for speed
        for (byte pixel=0; pixel<CH; pixel++) {
            WRITE_BUS(copy_buffer[i++]); 
            CLOCK_1; 
        }
    }
  }
  SET_X_RANGE(clear_start,clear_stop);
  SET_Y_LOCATION(0);
  tft.flood(bg,SW*abs(scroll_rows)*CH);
}

/** Store ("stash") current cursor location */
void save_cursor() {
  saved_row=row; saved_col=col;
}

/** Xor-draw the cursor at the current position. 
 *  Can be used to both add and erase the cursor.
 */
void cstamp() { 
  if (cursor_visible && col<TC)
    tft.invertRect(row*CH, col*CW, 1, CW);
}

/** Restore cursor from stashed position */
void restore_cursor() {
  cstamp();  
  row=saved_row; col=saved_col; 
  cstamp();  
}

/** Make cursor visible */
void show_cursor() {
  if (!cursor_visible) { cursor_visible=1; cstamp(); }
  else cursor_visible = 1;
}

/** Make cursor invisible */
void hide_cursor() {
  if (cursor_visible) cstamp();  
  cursor_visible = 0;
}

/** Backspace */
void backspace() {
  if (!col) return;
  cstamp(); 
  col--; 
  load_and_draw_glyph(' '); 
  cstamp();
}

/** Implement bell as screen flash */
void bell() {
  COMMAND(ILI9341_INVERTON); 
  bell_counter=0x7fff; 
}

/** Serial read, blocking until input is available */
uint8_t blocking_read()  {
  while (!Serial.available());
  return Serial.read();
}

/** Advance to first column of next row, scrolling up if needed.
 *  Remainder of this row is filled with the current background color.
 */
void newline() {
  // Move down without scrolling if possible
  if (row) {
    row--;
  } 
  else {
    // Scrolling is slow so we need to scroll multiple to keep up
    int nscroll=8;
    scroll(nscroll); 
    row=nscroll-1;
  } 
  col=0;
}


/** Update the blink flag information. The "blink machine" needs this
 *  to render blinking text correctly
 */ 
void update_blink(byte r, byte c) {
  // Update "blink" flag for this location in the "blinking" bitvector
  if (blink_mode==NORMAL) BVEC_CLEAR(blinking, r, c);
  else                    BVEC_SET(  blinking, r, c);
  BVEC_CLEAR(highlight, r, c);
}

/** Move cursor to next position, redrawing if needed, adding new line if needed
 *  This assumes that the current position has recently been drawn, so there is
 *  no need to "erase" the cursor there. Call "cstamp();" before calling this 
 *  routine if you need to xor-draw out the cursor before moving it.
 *  
 *  We don't automatically start a new line if the current line is full, only if
 *  we then continue to try to print. Filling the line, then sending \n, emits 
 *  only one newline. We can also send \r at the end of a full line to return to
 *  the beginning (not the start of the next line). 
 */
void advance_cursor(uint8_t n) {
  update_blink(row,col);
  // Tell the combining modifier code that it's OK to combine with the current
  // bitmap. Also tell it where to draw the combined character by saving the
  // current row and column. 
  prev_row = row;
  prev_col = col;
  new_combining_ok = 1;
  col += n;
  if (col>TC) newline();
  cstamp();
}

/** We don't immediately trigger a newline when adancing the cursor, but we
 *  DO need to trigger a newline if more characters are to be printed. This
 *  is called before printing to achieve this. 
 */
void prepare_cursor() {
  if (col>=TC) newline();
}

/** Print character, advancing 1 column. If already at last column, 
 *  increment row (scrolling if needed), and move back to column 0;
 */
void printch(char c)  {
  prepare_cursor();
  load_char_bitmap_11x5(font_6x12_glyphs+BYTESPERCHAR_GLYPHS*(c));
  drawCharFancy(CH*row,CW*col,fg,bg,font_weight,font_mode,HALFWIDTH);
  advance_cursor(1);
  cstamp();
}

/** Print null-terminated string
 */
void print(const char *s) {
  for (int i=0;i<1000;i++) {
    if (!s[i]) break; 
    printch(s[i]);
  }
}

/** Print null-terminated string with newline
 */
void println(const char *s) {
  print(s); 
  newline();
}

/** Reset all text attributes */
void reset_text_attributes() {
  invert = font_weight = blink_mode = underline_mode = overline_mode = strike_mode = font_mode = frame_mode = script_mode = NORMAL;
  blink_mode = NORMAL;
  fg = FG_DEFAULT;
  bg = BG_DEFAULT;
  ul = FG_DEFAULT;
}

/** Erases the character bitmap global state variable */
void clear_bitmap() { 
  for (int i=0; i<CH; i++) char_bitmap[i]=0;
}

/** Reset terminal to initial state */
void reset() {
  reset_text_attributes(); 
  cursor_visible=1; 
  combining_ok=0;
  reset_screen(); 
  clear_bitmap();
  clear_blink();
  cstamp();
}

#endif // TERMINAL_MISC_H
