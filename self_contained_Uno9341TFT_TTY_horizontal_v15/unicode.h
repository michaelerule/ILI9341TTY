#ifndef UNICODE_H
#define UNICODE_H

#include "terminal_misc.h"
#include "TFT_macros.h"

// Index of glyph to use when a character isn't found
#define REPLACEMENT_CHARACTER (0)

#define FIN {advance_cursor(1); return SUCCESS;}

// Non-ASCII glyph/character point definitions (indecies into the font bitmap)
int handle_transform(byte index, byte command);

// List of which blocks we intend to support, and datastructures to find
// the appropriate subroutine for each block, given a unicode point.
#include "unicode_blocks.h"

// Code to handle the combining diacritics block
#include "combining_diacritics.h"

//______________________________________________________________________________
// 0x000000-0x00007F: Basic Latin 
int _basiclatin(unsigned int c) {
  if (c>=0x20 && c<=0x7E) {
      load_glyph_bitmap(c);
      return LOADED;
  }
  return NOT_MAPPED;
}

// Code to handle software-rendered fonts
#include "softfonts.h"

////////////////////////////////////////////////////////////////////////////////
// A tight little binary search for unicode block subroutine index
int8_t binary_search(unsigned int i) {
  int8_t lo = 0;
  int8_t hi = NBLOCKS;
  while (hi>lo) {
    int8_t midpoint = (lo+hi)/2;
    unsigned int a = pgm_read_word(&block_starts_x16 [midpoint]);
    unsigned int b = pgm_read_byte(&block_lengths_x16[midpoint]) + a;
    if (i>=a) {
      if (i<b) return midpoint;
      lo=midpoint+1;
    }
    else hi=midpoint-1;
  }
  // Ran off beginning of list
  if (hi<lo) return (-1);
  // Handle high==low case: test and return if in range
  unsigned int a = pgm_read_word(&block_starts_x16 [lo]);
  unsigned int b = pgm_read_byte(&block_lengths_x16[lo]) + a;
  if (i>=a && i<b) return lo;
  return (-1);
}

////////////////////////////////////////////////////////////////////////////////
/** Dispatch unicode point to subroutines for handling various blocks and 
 *  range of codepoints.
 */
int load_unicode(uint32_t code) {
  //Report code in octal for debugging purposes
  // printch('['); 
  // for (int i=0; i<7; i++) printch('0'+((code>>(3*(6-i)))&0b111)); 
  // printch(']');
  // Fast-track ASCII
  if (code<128) return _basiclatin((byte)code);
  // Divide code by 16 to get its "row" in the uncode table
  unsigned int coderow = code>>4;
  // Skip codepoints past the end of the mapped blocks
  if (coderow>=LASTROW+1) return NOT_IMPLEMENTED;
  // Binary search to find function to handle this block
  int8_t search_result = binary_search(coderow);
  if (search_result>=0) {
    unsigned int block_start_row = pgm_read_word(&block_starts_x16[search_result]);
    return (*unicode_block[search_result])(code - block_start_row*16);
  }
  return NOT_IMPLEMENTED;
}

////////////////////////////////////////////////////////////////////////////////
/** Parse utf-8 encoded unicode codepoint. Based on the first byte, this will
 *  attempt to read up to 3 more bytes from the serial input. If a valid 
 *  unicode sequence is found, it will attempt to interpret and draw the 
 *  corresponding character. Returns FAIL if an invalid utf-8 sequence 
 *  encountered, or if there was an error in rendering the unicode point. If it
 *  cannot render the given unicode point, the replacement character <?> should
 *  be rendered instead. 
 *  @param byte1: first byte of a putative unicode sequence (we'll wait for 
 *      more if needed)
 */
int parse_utf8(byte byte1) {
  uint32_t code = byte1;
  if (byte1>=128) {
    int nbytes = 0;
    if      ((byte1>>5)==0b110  ) {code=byte1 & 0b11111; nbytes=1;}
    else if ((byte1>>4)==0b1110 ) {code=byte1 &  0b1111; nbytes=2;}
    else if ((byte1>>3)==0b11110) {code=byte1 &   0b111; nbytes=3;}
    if (!nbytes) return FAIL; // Ignore bad utf-8
    for (int j=0; j<nbytes; j++) {
      byte b = blocking_read();
      if (!((b>>6)==0b10)) return FAIL; // Ignore bad utf-8
      code = (code<<6)|(b&0b111111);}
  }
  //pause_incoming_serial();
  prepare_cursor();
  byte return_code = load_unicode(code);
  if (return_code == LOADED) {
    // Soft-fonts draw, but mapped fonts only load the character bitmap.
    // This allows the mathematical alphanumerics soft-font to re-use the
    // unicode mapping for Greek, without drawing to screen, in order to
    // further style characters before drawing. 
    drawStyledChar();
    advance_cursor(1);   
    //resume_incoming_serial();
    return SUCCESS;
  }
  else if (return_code != SUCCESS and return_code != NOT_MAPPED) {
    load_and_draw_glyph(REPLACEMENT_CHARACTER);
    advance_cursor(1);
  }
  //resume_incoming_serial();
  return return_code;
}


#endif /*UNICODE_H*/
