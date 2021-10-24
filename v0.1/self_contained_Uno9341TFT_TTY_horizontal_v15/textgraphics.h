#ifndef TEXTGRAPHICS_H
#define TEXTGRAPHICS_H

#include "myfont.h"

#define FONT(i) (pgm_read_byte((font_6x12_glyphs+i)))

////////////////////////////////////////////////////////////////////////////////
// Low-level routines for moving bits to/from memory and the display

/** Draw horizontal line one character wide (widths over 15 unsupported). */
void floodline(unsigned int x, unsigned int y, byte color, byte ncols) {
  SET_XY_RANGE(x,x,y); 
  COMMAND(BEGIN_PIXEL_DATA); 
  WRITE_BUS(color);
  // TODO: switching this to tft.flood will save space
  // The compiler will optimize this to inline the appropriate # clock pulses
  while (ncols--) tft.clockb(CW);// CLOCK_N(CW);
}

/** Transfer character bitmap to the screen at given location, expecting data
 *  packed in rows. One byte per row, with pixels left to right from the 
 *  lowest to highest-order bits. 
 *  @param x: x coordinate of lower-left of character (rendering sideways!)
 *  @param y: y coordinate of lower-left of character (rendering sideways!)
 *  @param chdata: Length CH array of character row data
 *  @param fg: foreground color in RRRBBGGG format
 *  @param bg: background color in RRRBBGGG format
 */
void blit_rowwise(unsigned int x, unsigned int y, byte *chdata, byte charwidth, byte fg, byte bg) {
  // Send data to screen. Data are packed in columns now. 
  SET_XY_RANGE(x,x+(CH-1),y);
  COMMAND(BEGIN_PIXEL_DATA);
  byte color = bg;
  byte b     = 0;
  WRITE_BUS(color);
  // Pad left, if fullwidth (full-width are just padded half-width for now)
  if (charwidth==FULLWIDTH) tft.clockb(CH*(CW>>1));
  for (int i=0; i<CW; i++) {
    for (int j=0; j<CH; j++) {
      byte nb = (chdata[j]>>i)&1;
      if (nb!=b) {b=nb; color=(b?fg:bg); WRITE_BUS(color);}
      CLOCK_1;
    }
  }
  // Pad right, if fullwidth (full-width are just padded half-width for now)
  if (charwidth==FULLWIDTH) { WRITE_BUS(bg); tft.clockb(CH*(CW-(CW>>1)));}
}

////////////////////////////////////////////////////////////////////////////////
// Bitmap manipulation routines: achieve font effects in software to reduce
// the number of base glyph bitmaps required.

/** Create a bold font by copying pixel data right one column
 *  - Overstamp right 1 pixel: Stamp left 5 columns onto middle 5 columns
 *  - Except don't over-stamp if the column to the right is filled
 *  - Also don't change the leftmost column (leave space between letters)
 */ 
void hboldright() {
  for (byte i=0; i<CH; i++) 
    char_bitmap[i] |= 
      (((char_bitmap[i]&CHARRIGHTMASK)<<1) 
      &~ ((char_bitmap[i]&CHARLEFTMASK)>>1)) & CHARLEFTMASK;
}

/** Create a bold font by copying pixel data left one column
 *  - Overstamp left 1 pixel: Stamp right 4 columns onto middle 4 columns
 *  - Except don't over-stamp if the column to the left is filled
 */ 
void hboldleft() {
  for (byte i=0; i<CH; i++) 
    char_bitmap[i] |= 
      (((char_bitmap[i]&CHARLEFTMASK)>>1) 
      &~ ((char_bitmap[i]&CHARRIGHTMASK)<<1)) & CHARLEFTMASK;
}

/** Italicize font by shifting bottom half to the left and filling in any gaps
 *  Gaps form when we have character data that looks like this:
 *  *01*  -->  *01
 *  *10*       10*
 *  if above-right is 1 and below-right is 0 and below is 1 and above is 0
 */
void italicize() {
  byte above = char_bitmap[SPLIT];
  byte below = char_bitmap[SPLIT-1];
  byte above_right = above>>1;
  byte below_right = below>>1;
  byte rejoin = above_right & ~below_right & below & ~above;
  for (byte i=0; i<SPLIT; i++) char_bitmap[i] >>= 1;
  char_bitmap[SPLIT-1] |= rejoin;
}

/** Outline font by copying to nearby pixels and subtracting original */
void outline() {
  byte curr = char_bitmap[0];
  byte next = char_bitmap[1];
  byte blur = curr|next;
  char_bitmap[0] = CHARROWMASK & (((blur<<1)|blur|(blur>>1)) & ~curr);
  byte prev = curr;
  curr = next;
  for (byte i=1; i<CH-1; i++) {
    next = char_bitmap[i+1];
    blur = prev|curr|next;
    char_bitmap[i] = CHARROWMASK & (((blur<<1)|blur|(blur>>1)) & ~curr);
    prev = curr;
    curr = next;
  }
  blur = prev|curr;
  char_bitmap[CH-1] = CHARROWMASK & (((blur<<1)|blur|(blur>>1)) & ~curr);
}

/** Invert font and encase characters in rounded-rectangle
 *  Used to render enclosed / encircled glyphs.
 */
void entomb() {
  char_bitmap[0   ] = (~char_bitmap[0   ])&CHARMIDDLEMASK;
  char_bitmap[CH-2] = (~char_bitmap[CH-1])&CHARMIDDLEMASK;
  for (byte i=1; i<CH-2; i++) 
    char_bitmap[i] ^= CHARROWMASK;
  char_bitmap[CH-1]=0;
}

/** Helper routine for various vertical shortening functions below. Copies
 *  character data downwards from the indicated starting row. 
 *  @param charrows: length CH (character height) byte*; (CW>8 unsupported)
 *  @param i: row to remove by copying all rows above down a row.
 */
void copy_down(byte i) {
   for (; i<CH-1; i++) char_bitmap[i] = char_bitmap[i+1]; 
   char_bitmap[CH-1]=0;
}

/** Shorten character toward baseline (if possible) to make room for diacritics 
 *  above.  This requires the character bitmap to  be packed by rows.  Bits are
 *  left-to-right from LOW TO HIGH within each row. Rows are packed from bottom
 *  to top.  I. e. The bottom left pixel is stored in the lowest bit of the 1st
 *  element of the charrows array.
 *  @param charrows: length CH (character height) byte*; (CW>8 unsupported)
 */
int shorten_down_top() {
  // Start from the top, work down.
  int i=CH-1;
  
  // First, find the top of the character
  while (!char_bitmap[i] && i>=BASELINE) i--;
  
  // Character seems already empty? If this happens it is a bug!
  if (i==BASELINE) return FAIL;
  
  // Now, work down looking for duplicated rows
  do {
    if (char_bitmap[i]==char_bitmap[i-1]) break;
    i--;
  } while (i>=BASELINE);
  
  // Could not squish character.
  if (i<=BASELINE) return FAIL;
  
  // Row i matches row i-1. Pull down from row i? 
  copy_down(i);
  return SUCCESS;
}

/** Nudge character downwards (if possible), to make room for diacritics above.
 *  This will destroy the baseline of the character, but might be preferable to
 *  ignoring a diacritic. 
 *  @param charrows: length CH (character height) byte*; (CW>8 unsupported)
 */
int nudge_down_top() {
  if (char_bitmap[0]) return FAIL;
  copy_down(0);
  return SUCCESS;
}

/** Remove vertical space between diacritics. Emergency effort to create space
 *  vertically if too many combining diacritics have been issued. This one is
 *  conservative, and does not remove whitespace if it would cause pixels to 
 *  collide vertically.
 *  @param charrows: length CH (character height) byte*; (CW>8 unsupported)
 */
int smash_diacritics_down_top_conservative() {
  for (int i=CH-2; i>BASELINE; i--) {
    if (!char_bitmap[i] && !(char_bitmap[i+1]&char_bitmap[i-1])) {
      copy_down(i);
      return SUCCESS;
    }
  }
  return FAIL;
}

/** Remove vertical space between diacritics. Emergency effort to create space
 *  vertically if too many combining diacritics have been issued. This version
 *  will allow pixels to collide, possibly obscuring the underlying meaning. 
 *  @param charrows: length CH (character height) byte*; (CW>8 unsupported)
 */
int smash_diacritics_down_top_aggressive() {
  for (int i=CH-2; i>BASELINE; i--) {
    if (!char_bitmap[i]) {
      copy_down(i);
      return SUCCESS;
    }
  }
  return FAIL;
}

/** Shorten character up to make room for diacritics BELOW. This starts at the
 *  base and works upwards, looking for duplicate rows which can be merged. 
 *  @param charrows: length CH (character height) byte*; (CW>8 unsupported)
 */
int shorten_up_base() {
  int i=0;
  while (!char_bitmap[i] && i<CH) i++;
  while (i<CH-1 && char_bitmap[i]!=char_bitmap[i+1]) i++;
  if (i>=CH-1) return FAIL;
  while (i>=1) {char_bitmap[i]=char_bitmap[i-1]; i--;}
  char_bitmap[0] = 0;
  return SUCCESS;  
}

/** Nudge character up to make room for diacritics BELOW.
 *  @param charrows: length CH (character height) byte*; (CW>8 unsupported)
 */
int nudge_up_base() {
  // Check if we can delete the top row
  if (char_bitmap[CH-1]) return FAIL;
  // Copy all character data upwards, starting at top
  for (int i=CH-1; i>=1; i--) char_bitmap[i] = char_bitmap[i-1]; 
  char_bitmap[0]=0;
  return SUCCESS;
}

/** Compress diacritics below to make room for diacritics BELOW, avoiding direct
 *  collisions between pixels. This operates only on diacritics below the 
 *  baseline first, but will remove whitespace above the baseline if that
 *  fails. 
 *  @param charrows: length CH (character height) byte*; (CW>8 unsupported)
 */
int smash_diacritics_up_base_conservative() {
  // Starting from the bottom and working upwards
  for (int i=1; i<MIDLINE; i++) {
    // Look for empty rows that can be removed without direct collisions
    if (!char_bitmap[i] && !(char_bitmap[i-1]&char_bitmap[i+1])) {
      // Remove row i and copy rows below upwards
      for (; i>=1; i--) char_bitmap[i]=char_bitmap[i-1];
      char_bitmap[0]=0;
      return SUCCESS; 
    }
  }
  return FAIL;
}
 
/** Compress diacritics below to make room for diacritics BELOW, allowing direct
 *  collisions between pixels. This attempts to delete whitespace from below the
 *  baseline, but will delete vertical whitespace elsewhere if that fails. For
 *  example, it will merge the "dot" withthe "stem" of the character 'i'.
 *  @param charrows: length CH (character height) byte*; (CW>8 unsupported)
 */
int smash_diacritics_up_base_aggressive() {
  // Starting from the bottom and working upwards
  for (int i=1; i<MIDLINE; i++) {
    // Look for empty rows that can be removed without direct collisions
    if (!char_bitmap[i]) {
      // Remove row i and copy rows below upwards
      for (; i>=1; i--) char_bitmap[i]=char_bitmap[i-1];
      char_bitmap[0]=0;
      return SUCCESS; 
    }
  }
  return FAIL;
}

/** Verify that loading and blitting character data row-wise work
 */
/*void test_blit_rowwise() {
  byte charrows[CH];
  int i=0;
  for (int r=0; r<8; r++) for (int c=0; c<32; c++) {
    load_character_bitmap_rowwise(i,charrows);
    blit_rowwise(r*CH*2,c*CW*2,charrows,HALFWIDTH,fg,bg);
    i++;
  }  
}
*/

////////////////////////////////////////////////////////////////////////////////
// Fancy character rendering subroutines. 

/** Blend two 8-bit RRRBBGGG colors 
 *
 */
byte fadecolor(byte c1, byte c2, byte a) {
  return (((a*(c1&RGMASK)+(3-a)*(c2&RGMASK)+2)>>2)&RGMASK) 
       | (((a*(c1& BMASK)+(3-a)*(c2& BMASK)+2)>>2)& BMASK);
}

/** Load character bitmaps from memory, combining up to to characters.
 *  Setting both characters to NULL clears the char_bitmap memory.
 *  This is used to load full 12x6 characters, in the box/block drawing 
 *  subroutines
 *  @param c1: pointer to PROGMAM byte * for start of first  glyph, or NULL
 *  @param c2: pointer to PROGMAM byte * for start of second glyph, or NULL
 */
void load_char_bitmaps_12x6(const byte *c1, const byte *c2) {
  // First copy raw data from memory, combining glyphs if needed
  // Read c1 (or fill with zeros if null). If c2 is not null, combine it.
  byte charbytes[BYTESPERCHAR_BOXDRAWING];
  if (!c1) for (byte j=0;j<BYTESPERCHAR_BOXDRAWING;j++) charbytes[j] = 0;
  else     for (byte j=0;j<BYTESPERCHAR_BOXDRAWING;j++) charbytes[j] = pgm_read_byte(c1+j);
  if (c2)  for (byte j=0;j<BYTESPERCHAR_BOXDRAWING;j++) charbytes[j]|= pgm_read_byte(c2+j);
  char_bitmap[ 0] =   charbytes[0]     & 0b00111111;
  char_bitmap[ 1] = ((charbytes[0]>>6) & 0b00000011) | ((charbytes[1]&0b00001111)<<2);
  char_bitmap[ 2] = ((charbytes[1]>>4) & 0b00001111) | ((charbytes[2]&0b00000011)<<4);
  char_bitmap[ 3] = ((charbytes[2]>>2) & 0b00111111);
  char_bitmap[ 4] =   charbytes[3]     & 0b00111111;
  char_bitmap[ 5] = ((charbytes[3]>>6) & 0b00000011) | ((charbytes[4]&0b00001111)<<2);
  char_bitmap[ 6] = ((charbytes[4]>>4) & 0b00001111) | ((charbytes[5]&0b00000011)<<4);
  char_bitmap[ 7] = ((charbytes[5]>>2) & 0b00111111);
  char_bitmap[ 8] =   charbytes[6]     & 0b00111111;
  char_bitmap[ 9] = ((charbytes[6]>>6) & 0b00000011) | ((charbytes[7]&0b00001111)<<2);
  char_bitmap[10] = ((charbytes[7]>>4) & 0b00001111) | ((charbytes[8]&0b00000011)<<4);
  char_bitmap[11] = ((charbytes[8]>>2) & 0b00111111);
}

/** Load character bitmaps from memory. This is used to load "normal" alphanumeric
 *  Glyphs. 
 *  @param c1: pointer to PROGMAM byte * for start of first  glyph, or NULL
 */
void load_char_bitmap_11x5(const byte *c1) {
  // First copy raw data from memory, combining glyphs if needed
  // Read c1 (or fill with zeros if null). If c2 is not null, combine it.
  byte charbytes[BYTESPERCHAR_GLYPHS];
  if (!c1) for (byte j=0;j<BYTESPERCHAR_GLYPHS;j++) charbytes[j] = 0;
  else     for (byte j=0;j<BYTESPERCHAR_GLYPHS;j++) charbytes[j] = pgm_read_byte(c1+j);
  // New version in for 11x5 packed data. 
  char_bitmap[ 0] =  (charbytes[0]<<1) & 0b111110;
  char_bitmap[ 1] = ((charbytes[0]>>4) & 0b1110 ) | ((charbytes[1] & 0b11  ) << 4);
  char_bitmap[ 2] =  (charbytes[1]>>1) & 0b111110;
  char_bitmap[ 3] = ((charbytes[1]>>6) & 0b10   ) | ((charbytes[2] & 0b1111) << 2);
  char_bitmap[ 4] = ((charbytes[2]>>3) & 0b11110) | ((charbytes[3] & 0b1   ) << 5);
  char_bitmap[ 5] =  (charbytes[3]>>0) & 0b111110;
  char_bitmap[ 6] = ((charbytes[3]>>5) & 0b110  ) | ((charbytes[4] & 0b111 ) << 3);
  char_bitmap[ 7] =  (charbytes[4]>>2) & 0b111110;
  char_bitmap[ 8] =  (charbytes[5]<<1) & 0b111110;
  char_bitmap[ 9] = ((charbytes[5]>>4) & 0b1110 ) | ((charbytes[6] & 0b11  ) << 4);
  char_bitmap[10] =  (charbytes[6]>>1) & 0b111110;
  char_bitmap[11] = 0;
}

////////////////////////////////////////////////////////////////////////////////
/** Fancy version of drawchar, applying font effects.
 *  This assumes that the desired character is loaded into char_bitmap.
 *  It modifies the contents of char_bitmap in place if font styling
 *  is set. 
 * @param x: x location to draw on screen, in pixels
 * @param y: y location to draw on screen, in pixels
 * @param fg: forgreound color, in 8-bit RRRBBGG format
 * @param bg: background color, in 8-bit RRRBBGG format
 * @param weight: NORMAL, BOLD, or FAINT
 * @param font: NORMAL, ITALIC, OUTLINE, TABLET, FRAKTUR
 * @param charwidth: HALFWIDTH, FULLWIDTH
 */
void drawCharFancy(unsigned int x, unsigned int y, 
                   byte fg, byte bg, 
                   byte weight, byte font, byte charwidth) {
                     
  if (invert) {byte temp=fg; fg=bg; bg=temp;}
  
  // Apply font syle transformations to the current char_bitmap
  switch (weight)  {
    case NORMAL: break;
    case BOLD:   hboldright(); break;
    case FAINT:  fg = fadecolor(fg,bg,3); break;
  }
  switch (font)  {
    case NORMAL:  break;
    case ITALIC:  italicize(); break; 
    case OUTLINE: outline();   break;
    case TABLET:  entomb();    break;
    case FRAKTUR: 
      hboldright();
      hboldleft(); 
      break;
  }
  
  // Send to screen  
  blit_rowwise(x, y, char_bitmap, charwidth, fg, bg);
  
  // Draw underlines, overlines, and strike-through
  // (Extend under/over/strike lines for full-width characters)
  byte ncols = charwidth==FULLWIDTH?2:1;
  switch (underline_mode) {
    case NORMAL: break;
    case DOUBLE: floodline(x+2,y,ul,ncols);
    case SINGLE: floodline(x,  y,ul,ncols);
  }
  switch (overline_mode) {
    case NORMAL: break;
    case DOUBLE: floodline(x+CH-4,y,ul,ncols);
    case SINGLE: floodline(x+CH-2,y,ul,ncols);
  }  
  if (strike_mode == STRIKE) floodline(x+(CH/2)-1,y,ul,ncols);
}

/** Shortcut to load a glyph from the main font map. 
 *  This routine only reads from the variable font_6x12_glyphs
 *  Currently only supports up to 256 base glyphs
 *  Currently only supports 12x6 characters, (row-major packed)
 */
#define load_glyph_bitmap(glyph_index) {load_char_bitmap_11x5(font_6x12_glyphs+BYTESPERCHAR_GLYPHS*(glyph_index));}

/** Shortcut to draw whatever is in char_bitmap with current styling flags 
 */
#define drawStyledChar() {drawCharFancy(CH*row,CW*col,fg,bg,font_weight,font_mode,HALFWIDTH);}

/** Shortcut to load and draw half-width glyph with current style at current cursor location
 */
#define load_and_draw_glyph(c) {load_glyph_bitmap(c); drawStyledChar();}


#endif //TEXTGRAPHICS_H
