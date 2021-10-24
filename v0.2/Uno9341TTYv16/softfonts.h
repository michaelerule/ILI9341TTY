#ifndef SOFTFONTS_H
#define SOFTFONTS_H

////////////////////////////////////////////////////////////////////////////////
// Packed data for various blocks


// Glyph indecies for for enclosed alphanumerics; 0-20 a-z A-Z
static const byte enclosed_map[] PROGMEM = { 84, 59, 60, 61, 62, 63, 64, 65, 66,
 67,146,147,148,149,150,151,152,153,154,155,156,  4,182,  5,183,  6,184, 42,185,
186,205,187,188,  7,  8,  9, 43, 44, 10, 11,189, 12, 13, 14, 15, 45, 16, 70, 71,
 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85,179, 86, 87, 88, 89, 90,
 91, 92, 93, 94,};


// Glyph indecies for for mathematical alphanumerics; AZa𝚤 𝚥AΩ𝛁αω𝜕𝜖𝜗𝜘𝜙𝜚𝜛
static const byte alphanumerics_map[] PROGMEM = { 70, 71, 72, 73, 74, 75, 76,
 77, 78, 79, 80, 81, 82, 83, 84, 85,179, 86, 87, 88, 89, 90, 91, 92, 93, 94,  4,
182,  5,183,  6,184, 42,185,186,205,187,188,  7,  8,  9, 43, 44, 10, 11,189, 12,
 13, 14, 15, 45, 16, 19, 48, 70, 71,108,109, 74, 94, 77,100, 78, 80,106, 82, 83,
110, 84,111, 85,100,101, 88, 93,112, 92,113,114,144, 25,209, 50,194, 22,210, 47,
195, 26, 20,115, 46, 13,211,  9, 27, 51, 52, 28, 29, 12, 53, 54,212, 30,143, 33,
196, 32,208, 55, 31, 75,207, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67,};


// Unicode points for half-width kana substitutes:
static const unsigned int halffullmap[] PROGMEM = {111, 91, 93, 44,12539,12530,
12449,12451,12453,12455,12457,12515,12517,12519,12483,12540,12450,12452,12454,
12456,12458,12459,12461,12463,12465,12467,12469,12471,12473,12475,12477,12479,
12481,12484,12486,12488,12490,12491,12492,12493,12494,12495,12498,12501,12504,
12507,12510,12511,12512,12513,12514,12516,12518,12520,12521,12522,12523,12524,
12525,12527,12531,12443,12444,};



//..............................................................................
// Codes defining arrangements of "quadrants" from the block drawing block
static const byte quadrantmap[5] PROGMEM = {
  0b01001000,0b11100010,0b10110110,0b00010111,0b11011001
};

  
//..............................................................................
/** The Symbols for legacy computing block defines "teletext characters" in the
 *  range 0x1FB3C-0x1FB67. There should be 44 of these, but the latter half are
 *  just inverted copies of the first 22. Each character can be rendered as a
 *  filled, sloping line. We define an initial y position for this line, as well
 *  as its slope. We then move horizontally, filling in pixels below the y
 *  coordinate as we go. Each character can be idenfied by its starting
 *  y-position and slope. Characters are divided into 3 sections vertically, 
 *  demarcated by endpoints 0,1,2,3. Slope is the change in height per character
 *  width, ranging from -6 to +6. We encode slope and y0 as an array of byte.
 *  The top 4 bits are the starting position and the bottom 4 are the slope. 
 * 
 * Raw y0 codes
 * 1 1 2 2 3 2 2 1 1 0 1 -1 0 -2 0 -3 4 3 5 3 6 2
 *
 * Raw slope codes: (divide by 2 to get actual slope)
 * -2,-1,-4,-2,-6,3,1,4,2,6,1,2,1,4,2,6,-2,-1,-4,-2,-6,-1
 *
 * Python code to generate lookup table: 
 * ','.join(['0x%X'%i for i in (array([
 *   1,1,2,2,3,2,2,1,1,0,1,-1,0,-2,0,-3,4,3,5,3,6,2
 *   ])+3)*16+array([
 *   -2,-1,-4,-2,-6,3,1,4,2,6,1,2,1,4,2,6,-2,-1,-4,-2,-6,-1
 *   ])+6])
 * 
 *  For now, this code is specialized for 12x6 characters.
 */
// Slope and intercept data for teletext characters
#define NTELETEXT (22)
static const byte teletext_map[NTELETEXT] PROGMEM = {
  0x44,0x45,0x52,0x54,0x60,0x59,0x57,0x4A,0x48,0x3C,0x47,
  0x28,0x37,0x1A,0x38,0xC,0x74,0x65,0x82,0x64,0x90,0x55
};



////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
// Subroutines used by block-rendering routines

////////////////////////////////////////////////////////////////////////////////
/** Print block sextant semigraphics (3x2). This code expects the character
 *  height CH to be a multiple of 3 and the character width CW to be a multiple
 *  of 2. Bits, from low to high, are ordered left-to-right then top-to-bottom.
 *  Codes for the empty character, full character, and left/right half bocks
 *  are not included in this range. 
 */
#define SEXTANTW (CW/2)
#define SEXTANTH (CH/3)
int handle_sextant(byte code) {
  // There are 4 missing tiles: blank, full, and left/right half bar
  byte b = code&0xff;   // 0b111111 is missing
  if (code>39) b++;     // 1fb27 missing one that follows
  if (code>19) b++;     // 1fb13 missing one that follows
  b ++;                 // 0 is missing
  SET_XY_RANGE(row*CH,row*CH+(CH-1),col*CW);
  COMMAND(BEGIN_PIXEL_DATA);
  byte color[2];
  color[0] = invert?fg:bg;
  color[1] = invert?bg:fg;
  for (byte c=0; c<2; c++) for (byte cr=0; cr<SEXTANTW; cr++) for (byte r=0; r<3; r++) {WRITE_BUS(color[(b>>(c+(2-r)*2))&1]); tft.clockb(SEXTANTH);}
  advance_cursor(1); 
  return SUCCESS;
}

////////////////////////////////////////////////////////////////////////////////
/* Subroutine for drawing teletext characters. 
 * also used for geometric shapes 0x25e2-25e54
 */
void draw_ttxt(int m0, int y0, byte color1, byte color2) {
  // Slope codes range from -6 to +6.
  // Convert to dy/dx in pixels
  int m = (m0*CH)/(CW+1);
  // y0 can range from -2 to 5. 0 is the base, 
  // 3 the top. Adjust accordingly.
  int y = (y0*CH*2+1)/3;
  SET_XY_RANGE(row*CH,row*CH+(CH-1),col*CW);
  COMMAND(BEGIN_PIXEL_DATA);
  for (byte c=0; c<CW; c++) {
    int a = max(0,min(CH,y>>1));    
    if (a>0) {WRITE_BUS(color1); tft.clockb(a);}
    a = CH-a;
    if (a>0) {WRITE_BUS(color2); tft.clockb(a);}
    y += m;
  }
}


////////////////////////////////////////////////////////////////////////////////
/** Draw teletext character 0x1FB3C-0x1FB67 */
int handle_teletext(byte b) 
{
  byte flip = invert;
  if (b >= 22) {flip=!flip; b-= 22;}
  byte color1 = flip? bg : fg;
  byte color2 = flip? fg : bg;
  byte code = pgm_read_byte(teletext_map+b);
  draw_ttxt((code&15)-6, (code>>4)-3, color1, color2);
  advance_cursor(1);
  return SUCCESS;
}



//______________________________________________________________________________
// 0x002100-0x00214F: Letterlike Symbols 
// 0x00002100-0x0000214F: Letterlike Symbols : this is defined as a mapping in myfont.h
/*
int _letterlikesymbols(unsigned int c) {
  // These need to map into the mathematical alphanumerics blocks
  int remap = -1;
  switch (c) {
    case  2: remap=0x138+0x02; break; // ℂ
    case 11: remap=0x09C+0x07; break; // ℋ
    case 12: remap=0x104+0x07; break; // ℌ
    case 13: remap=0x138+0x07; break; // ℍ
    case 16: remap=0x09C+0x08; break; // ℐ
    case 17: remap=0x104+0x08; break; // ℑ
    case 18: remap=0x09C+0x0B; break; // ℒ
    case 21: remap=0x138+0x0D; break; // ℕ
    case 25: remap=0x138+0x0F; break; // ℙ
    case 26: remap=0x138+0x10; break; // ℚ
    case 27: remap=0x09C+0x11; break; // ℛ
    case 28: remap=0x104+0x11; break; // ℜ
    case 29: remap=0x138+0x11; break; // ℝ
    case 36: remap=0x138+0x19; break; // ℤ
    case 40: remap=0x104+0x19; break; // ℨ
    case 44: remap=0x09C+0x01; break; // ℬ
    case 45: remap=0x104+0x02; break; // ℭ
    case 48: remap=0x09C+0x04; break; // ℰ
    case 49: remap=0x09C+0x05; break; // ℱ
    case 51: remap=0x09C+0x0C; break; // ℳ
    default: return NOT_IMPLEMENTED;
  }
  if (remap<0) return NOT_IMPLEMENTED;
  return _mathematicalalphanumericsymbols(remap);
} 
*/

//______________________________________________________________________________
// 0x002460-0x0024FF: Enclosed Alphanumerics 
/*
Run this in Python to find indecies for ranges that can be mapped to ascii: 
print(ord('①')-ord('①'))
print(ord('⑴')-ord('①'))
print(ord('⒈')-ord('①'))
0
20
40
print(ord('⒜')-ord('①'))
print(ord('Ⓐ')-ord('①'))
print(ord('ⓩ')-ord('①'))
print(ord('⓵')-ord('①'))
60
86
137
149
*/
byte load_glyph_bitmap(unsigned int base_glyph);
int _enclosedalphanumerics(unsigned int c) {
  //return NOT_IMPLEMENTED;
  if (c>=160) return NOT_MAPPED;
  if (c<60) {
    // Enclosed Numbers
    c = c+1;
    while (c>20) c-=20;
  }
  else {
    // Enclosed letters
    if      (c<112) c=c-60+21;
    else if (c<138) c=c-112+21;
    else if (c<139) c=0;
    else if (c<149) c=c-139+1+10;
    else if (c<159) c=c-149+1;
    else c=0;
  }
  load_glyph_bitmap(pgm_read_byte(enclosed_map+c));
  entomb();
  return LOADED;
}

//______________________________________________________________________________
// 0x002500-0x00257F: Box Drawing 
/** Box drawing characters. We define bitmaps for single and double line
 *  characters. Bold characters are rendered by combining single and double-line
 *  forms, as are any characters that mix sing/double lines. The array "boxdrawingmap"
 *  contains a 1-byte code for each drawing character, indicating  which single-line
 *  character to use in the top 4 bits, and which double-line character to use in 
 *  the lower 4 bits. Certain unusal characters in the box-drawing range are handled
 *  as a special case, and are assigned their own bitmaps. 
 *
 *  Each single/double line form has 16 forms, ordered based on binary presence
 *  of segements, clockwise, from left. Box codes therefore consist of 8 bits:
 *  and index for the single line, then doulble line, forms. Missing codes are
 *  zero.
 *
 * The first 12 characters are irregular. Codes 12-76 follow a regular pattern:
 * A single-line base character followed by three variations. We pack each into
 * 4-bit codes. Base characters are the same for every 4 characters so we don't
 * need to store as many.
 *
 * This got messy. The following Python code was used to generate
 * the packed data for points 12-76. 
s='''0b11000000,0b11000100,0b11001000,0b11001100,
  0b10010000,0b10010001,0b10011001,0b10011001, 0b01100000,0b01100100,0b01100010,0b01100110, 
  0b00110000,0b00110001,0b00110010,0b00110011, 0b11100000,0b11100100,0b11100010,0b11101000,
  0b11101010,0b11100110,0b11101100,0b11101110, 0b10110000,0b10110001,0b10110010,0b10111000, 
  0b10111010,0b10110011,0b10111001,0b10111011, 0b11010000,0b11010001,0b11010100,0b11010101,
  0b11011000,0b11011001,0b11011100,0b11011101, 0b01110000,0b01110001,0b01110100,0b01110101, 
  0b01110010,0b01110011,0b01110110,0b01110111, 0b11110000,0b11110001,0b11110100,0b11110101,
  0b11110010,0b11111000,0b11111010,0b11110011, 0b11110110,0b11111001,0b11111100,0b11110111, 
  0b11111101,0b11111011,0b11111110,0b11111111,'''
s  = [l[2:] for l in ''.join(s.strip().split()).split(',') if len(l)]
print(len(s))
c1 = [l[:4] for l in s ][::4]
c2 = [l[4:] for l in s ]
if len(c1)%2==1:
    c1 += ['0000']
#print(','.join(s))
print('// 4-bit packed character 1 for code ranges 12-80, in groups of 4')
print('// Lower (even) indecies occupy lower 4 bites')
print('// Higher (odd) indecies occupy upper 4 bites')
print(','.join(['0b%s%s'%(b,a) for (a,b) in zip(c1[::2],c1[1::2])]))
print('// 4-bit packed character 2 for code ranges 12-80, one per character')
print(','.join(['0b%s%s'%(b,a) for (a,b) in zip(c2[::2],c2[1::2])]))
 */
// 4-bit packed character 1 for code ranges 12-76, in groups of 4
// Lower (even) indecies occupy lower 4 bites
// Higher (odd) indecies occupy upper 4 bites
static const byte boxdrawingmap_char1[] PROGMEM = {
0b10011100,0b00110110,0b11101110,0b10111011,0b11011101,0b01110111,0b11111111,0b11111111
};
// 4-bit packed character 2 for code ranges 12-80, one per character
static const byte boxdrawingmap_char2[] PROGMEM = {
0b01000000,0b11001000,0b00010000,0b10011001,0b01000000,0b01100010,0b00010000,
0b00110010,0b01000000,0b10000010,0b01101010,0b11101100,0b00010000,0b10000010,
0b00111010,0b10111001,0b00010000,0b01010100,0b10011000,0b11011100,0b00010000,
0b01010100,0b00110010,0b01110110,0b00010000,0b01010100,0b10000010,0b00111010,
0b10010110,0b01111100,0b10111101,0b11111110
};
// Codes for indecies above 80, these are irregular
static const byte boxdrawingmap2[] PROGMEM = {
0b00000101,0b00001010,0b10000100,0b01001000, 0b00001100,0b10000001,0b00011000,0b00001001, 
0b00100100,0b01000010,0b00000110,0b00100001, 0b00010010,0b00000011,0b10100100,0b01001010,
0b00001110,0b10100001,0b00011010,0b00001011, 0b10000101,0b01011000,0b00000111,0b00100101, 
0b01010010,0b00000111,0b10100101,0b01011010, 0b00001111,0b11000000,0b10010000,0b00110000,
0b01100000,0b00000000,0b00000000,0b00000000, 0b00010000,0b00100000,0b01000000,0b10000000, 
0b00010001,0b00100010,0b01000100,0b10001000, 0b01010100,0b10101000,0b01010001,0b10100010
};
int _boxdrawing(unsigned int b) {
  if (b>127) return NOT_MAPPED;
  const byte *c1=0;
  const byte *c2=0;
  byte s = 0;
  if (b<12) {
    // Handle first 12 as a special case
    byte i1 = b&0b11;
    switch (b>>2) {
      case 0:
        // Code +5 is horizontal, +10 vertical
        c1 = font_6x12_boxdrawing + BYTESPERCHAR_BOXDRAWING*(5<<((b>>1)&1));
        // If odd, bold it by adding a double-line character
        if (b&1) c2 = c1 + BYTESPERCHAR_BOXDRAWING*16;
      break;
      case 1: c1 = font_6x12_boxdrawing+BYTESPERCHAR_BOXDRAWING*(36+i1); break;
      case 2: c1 = font_6x12_boxdrawing+BYTESPERCHAR_BOXDRAWING*(40+i1); break;
    }
  }
  else if (b<76) { 
    // Densely packed (regular) data.
    b -= 12;
    // Get first character code byte (these are lumped in groups of 4)
    byte b1 = pgm_read_byte(boxdrawingmap_char1 + (b>>3));
    // If b/4 is odd, C1 coded in the upper 4 bits
    if ((b>>2)&1) b1>>=4;
    b1 &= 0b1111;
    if (b1) c1 = font_6x12_boxdrawing+BYTESPERCHAR_BOXDRAWING*b1;
    // Get the second character code byte
    byte b2 = pgm_read_byte(boxdrawingmap_char2 + (b>>1));
    // If b is odd, C2 coded in the upper 4 bits
    if (b&1) b2>>=4;
    b2 &= 0b1111;
    if (b2) c2 = font_6x12_boxdrawing+BYTESPERCHAR_BOXDRAWING*(16+b2);
  } 
  else if (b<80) {
    // Odd group of 4 here, they have theor own glyphs
    byte i1 = b&0b11;
    c1 = font_6x12_boxdrawing+BYTESPERCHAR_BOXDRAWING*(32+i1);
  }
  else if (b>=113 && b<=115) {
    // Another irregular group
    if (b&0b01) c1=font_6x12_boxdrawing+BYTESPERCHAR_BOXDRAWING* 0;
    if (b&0b10) c2=font_6x12_boxdrawing+BYTESPERCHAR_BOXDRAWING*16;
  }
  else {
    // character can be rendered by combining single and double-line box primitives
    s = pgm_read_byte(boxdrawingmap2 + b - 80);
    byte i1 = s>>4;
    byte i2 = s&0b1111;
    if (i1) c1 = font_6x12_boxdrawing+BYTESPERCHAR_BOXDRAWING*i1;
    if (i2) c2 = font_6x12_boxdrawing+BYTESPERCHAR_BOXDRAWING*(i2+16);
  }
  // Prepare bitmaps
  load_char_bitmaps_12x6(c1,c2);
  // Box drawing ignores font styling
  drawCharFancy(CH*row,CW*col,fg,bg,NORMAL,NORMAL,HALFWIDTH);
  advance_cursor(1); 
  return SUCCESS;
}

//______________________________________________________________________________
// 0x002580-0x00259F: Block Elements 
int _blockelements(unsigned int b) {
  tft.fillRect(row*CH,col*CW,CH,CW,invert?fg:bg);
  byte  r=row*CH, h=CH, w=CW, color=invert?bg:fg, quadrant=0xff;
  unsigned int c=col*CW;
  if (b<16) { // Partial fill blocks
    if (b==0) {r+=(CH>>1); h=CH-(CH>>1);} // upper half block
    else if (b&8) w=((8-(b&7))*6+5)>>3;   // Left half blocks
    else h=(b*CH+5)>>3;                   // bottom half blocks
  } else { // other things
    switch (b&0xf) {
      case  0: c+=CW>>1; w=CW-(CW>>1); break; //right half block
      case  1: color = fadecolor(fg,bg,invert?3:1); break; // faint shade
      case  2: color = fadecolor(fg,bg,2); break; // middle shade
      case  3: color = fadecolor(fg,bg,invert?1:3); break; // dark shade
      case  4: r+=(CH*7)/8; h=CH-(CH*7)/8; break; // upper 1/8th block
      case  5: c+=(CW*7)/8; w=CW-(CW*7)/8; break; // right 1/8th block
      default: {
        byte i = (b&0xf)-6;
        quadrant = (pgm_read_byte(quadrantmap+(i>>1))>>((i&1)*4))&0xF;
      }
    }
  }
  if (quadrant==0xff) tft.fillRect(r,c,h,w,color);
  else {
    byte c1 = invert?bg:fg;
    byte c2 = invert?fg:bg;
    tft.fillRect(r        ,c        ,CH>>1     ,CW>>1     ,(quadrant&8)?c1:c2);
    tft.fillRect(r        ,c+(CW>>1),CH>>1     ,CW-(CW>>1),(quadrant&4)?c1:c2);
    tft.fillRect(r+(CH>>1),c        ,CH-(CH>>1),CW>>1     ,(quadrant&2)?c1:c2);
    tft.fillRect(r+(CH>>1),c+(CW>>1),CH-(CH>>1),CW-(CW>>1),(quadrant&1)?c1:c2);
  } 
  advance_cursor(1); 
  return SUCCESS;
}

//______________________________________________________________________________
/** Use braille patterns like semigraphics; char width (height) must be a multiple of 2 (4);
 *  Bits, from low to high, are stored top-to-bottom then left-to-right 
 */
#define BRAILLEW (CW>>1)
#define BRAILLEH (CH>>2)
int _braillepatterns(unsigned int b) {
  SET_XY_RANGE(row*CH,row*CH+(CH-1),col*CW); COMMAND(BEGIN_PIXEL_DATA);
  byte color[2]; color[0] = invert?fg:bg; color[1] = invert?bg:fg;
  for (byte c=0; c<2; c++) for (byte cr=0; cr<BRAILLEW; cr++) for (byte r=0; r<4; r++) {
    WRITE_BUS(color[(b>>(c*4+(3-r)))&1]); 
    tft.clockb(BRAILLEH);
  }
  advance_cursor(1);
  return SUCCESS;
}

//______________________________________________________________________________
// 0x00FF00-0x00FFEF: Halfwidth and Fullwidth Forms 
// Unicode points for half-width kana substitutes:
static const unsigned int extrafull[] PROGMEM = {
162, 163, 172, 175, 166, 165, 8361};
static const unsigned int extranormal[] PROGMEM = {
124, 8592, 8593, 8594, 8595, 9632, 9675};
int draw_fullwidth() {
  if (col == TC-1) newline();
  drawCharFancy(CH*row,CW*col,fg,bg,font_weight,font_mode,FULLWIDTH);
  advance_cursor(2);
  return SUCCESS;
}
int _halfwidthandfullwidthforms(unsigned int index) {
  if (index>=239) return NOT_MAPPED;
  // Up through index 94 is just a copy of ASCII
  // Then come half-width Katakana, but their order differs from the unicode Katakana block
  // Half width Hangul we do not implement
  // Then we get a row of full-width symbols ￠￡￢￣￤￥￦￨￩￪￫￬￭￮
  if (index<=94) {
    // Load character
    // Make space for double-wide character if needed
    // Draw at current location, padding to full-width
    load_unicode(index + ' ');
    return draw_fullwidth();
  }
  if (index<=96) {
    // These are full-width left/right parentheses
    // Draw these as outline full-width parentheses
    load_unicode(index - 95 + '(');
    outline();
    return draw_fullwidth();
  }
  if (index<=159) {
    // These are half width kana. Since our Katakana are already being rendered
    // as half width, there is not much to change. But, their order is different
    // and some of the combining diacritics are not diacritics. I don't want to
    // create extra "base glyphs", so we'll look these up based on unicode
    // codepoint. This also means we don't need to re-generate a lookup table
    // into the glyph code page(s) every time we change the font. 
    return load_unicode(pgm_read_word(halffullmap + index - 97));
  }
  if (index<224) {
    // Skipping half-wdith Hangul
    return NOT_IMPLEMENTED;
  }
  if (index<231) {
    // These are some full-width forms for ¢£¬¯¦¥₩
    load_unicode(pgm_read_word(extrafull + index - 224));
    return draw_fullwidth();
  }
  if (index==231) return NOT_MAPPED;
  // These are some half-width forms with normal aliases
  // |←↑→↓■○
  return load_unicode(pgm_read_word(extranormal + index - 232));
} 


//______________________________________________________________________________
// 0x01D400-0x01D7FF: Mathematical Alphanumeric Symbols 
// Glyph indecies for for mathematical alphanumerics; AZa𝚤 𝚥AΩ𝛁αω𝜕𝜖𝜗𝜘𝜙𝜚𝜛
int _mathematicalalphanumericsymbols(unsigned int index) {
  if (index>1023) return NOT_MAPPED;
  // Style defaults (these will change)
  byte  fw    = font_weight;
  byte  fm    = font_mode;
  byte  style = 0;
  byte  glyph = 0xFF;
  // Fancy math blocks; Implement these as alt-font rendering of latin/greek/numbers/symbols
  if (index<=675) { 
    // latin, 2x26=52 chars, 12 fonts
    // Modulo 52 (loop is faster than style=index/52, index=index%52)
    while (index>= 52) { style++; index-=52; }
    glyph = index;
    switch (style) {
      case  0: fw=BOLD;   fm=NORMAL;  break; // Bold font
      case  1: fw=NORMAL; fm=ITALIC;  break; // Italic font
      case  2: fw=BOLD;   fm=ITALIC;  break; // Bold + Italic
      case  3: fw=FAINT;  fm=ITALIC;  break; // Faint italic in lieu of fancy cursive
      case  4: fw=NORMAL; fm=ITALIC;  break; // Normal italic for regular cursive
      case  5: fw=NORMAL; fm=FRAKTUR; break; // Fraktur is just "very bold"
      case  6: fw=NORMAL; fm=OUTLINE; break; // Double-struck is just "outline"
      case  7: fw=BOLD;   fm=FRAKTUR; break; // Bold Fraktur is just "very very bold"
      case  8: fw=NORMAL; fm=NORMAL;  break; // Regular
      case  9: fw=BOLD;   fm=NORMAL;  break; // Bold Sans-serif
      case 10: fw=NORMAL; fm=ITALIC;  break; // Italic Sans-serif
      case 11: fw=BOLD;   fm=ITALIC;  break; // Bold Italic Sans-serif
      case 12: fw=NORMAL; fm=TABLET;  break; // In lieu of monospace
    }
  } else if (index<=679) {
    // some weird latin
    // 676: dotless i, italic
    // 677: dotless j, italic
    // 678: none
    // 679: none
    glyph = index-676;
    if (glyph>=2) return NOT_MAPPED;
    glyph += 52;
    fw = NORMAL; 
    fm = ITALIC;
  } else if (index<=969) {
    // greek, 58 chars, 5 fonts
    // Α..Ω (25) then ∇ (1) then α..ω (25) then ∂ ϵ ϑ ϰ ϕ ϱ ϖ
    index -= 680;
    while (index>=58) { style++; index-=58; }
    glyph = index + 54;
    switch (style) {
      case  0: fw=BOLD;   fm=NORMAL;  break; // Bold
      case  1: fw=NORMAL; fm=ITALIC;  break; // Italic
      case  2: fw=BOLD;   fm=ITALIC;  break; // Bold Italic
      case  3: fw=NORMAL; fm=FRAKTUR; break; // Bold sans, but we'll do very-bold
      case  4: fw=NORMAL; fm=OUTLINE; break; // Bold italic sans, but we do outline
    }
  } else if (index<=973) { 
    // extra greek: 
    // 970: uppercase digamma
    // 971: lowrecase digamma
    // 972: not mapped
    // 973: not mapped
    glyph = index-970;
    if (glyph>=2) return NOT_MAPPED;
    glyph += 112;
    fw=BOLD;   
    fm=NORMAL;
  } else { 
    // numbers 0-9, 5 fonts
    index -= 974;
    while (index>= 10) {style++; index-=10;}
    glyph = index+114;
    switch (style) {
      case  0: fw=BOLD;   fm=NORMAL;  break; // Bold
      case  1: fw=NORMAL; fm=OUTLINE; break; // Outline in lieu of doublestruck
      case  2: fw=NORMAL; fm=ITALIC;  break; // Italic in lieu of sans
      case  3: fw=BOLD;   fm=ITALIC;  break; // Bold italic in lieu of bold sans
      case  4: fw=NORMAL; fm=TABLET;  break; // Entombed in lieu of monospace
    }  
  }
  load_glyph_bitmap(pgm_read_byte(alphanumerics_map+glyph));
  // Draw with override style.
  drawCharFancy(CH*row, CW*col, fg, bg, fw, fm, HALFWIDTH);
  advance_cursor(1);
  return SUCCESS;
}

//______________________________________________________________________________
// 0x01F100-0x01F1FF: Enclosed Alphanumeric Supplement 
int _enclosedalphanumericsupplement(unsigned int c) {
  return NOT_IMPLEMENTED;
} 

//______________________________________________________________________________
// 0x01FB00-0x01FBFF: Symbols for Legacy Computing
// start  ing index in boxdrawing texture for chraacters from Legacy Computing 
#define LEGACY_COMPUTING_BITMAP_START (32*1+4*3) 
int _symbolsforlegacycomputing(unsigned int c) {
  if (c<60)  return handle_sextant(c);
  if (c<104) return handle_teletext(c-60); 
  // Rest of this block are provided as bitmaps
  // Six secret bonus glyphs
  if (c<203+6) 
    load_char_bitmaps_12x6(font_6x12_boxdrawing + BYTESPERCHAR_BOXDRAWING*(LEGACY_COMPUTING_BITMAP_START + c - 104),0);
  else if (c<240) return NOT_MAPPED;
  else if (c<250)
    load_char_bitmaps_12x6(font_6x12_boxdrawing + BYTESPERCHAR_BOXDRAWING*(
      LEGACY_COMPUTING_BITMAP_START + c - 240 + 98 + 7),0);
    // Box drawing ignores font styling
    drawCharFancy(CH*row,CW*col,fg,bg,NORMAL,NORMAL,HALFWIDTH);
    return LOADED;
  
  return NOT_MAPPED;
} 

//______________________________________________________________________________
// 0x01F100-0x01F1FF: Enclosed Alphanumeric Supplement 
int handle_unicode_mapping_table(byte blocktype, byte i, byte c);
int _geometricshapes(unsigned int c) {
  if (c>94) return NOT_IMPLEMENTED;
  // Special case: Some parts of geometric shapes stores elsewhere
  switch (c) {
    // Semigraphic-like geometric shapes (design to combine)
    case 54: return _symbolsforlegacycomputing(207); // ◖
    case 55: return _symbolsforlegacycomputing(208); // ◗
  }
  // Some stray symbols in the geometric symbols block that should 
  // be interpreted like teletext characters
  if (c>=66 && c<=69) {
    uint8_t color1 = invert? bg : fg;
    uint8_t color2 = invert? fg : bg;
    switch (c) {
      // 1/3 in 1 is slope 1 so 3/3 in one is slope 3
      case 66:  draw_ttxt( 3, 0, color1, color2); break; // ◢
      case 67:  draw_ttxt(-3, 3, color1, color2); break; // ◣
      case 68:  draw_ttxt( 3, 0, color2, color1); break; // ◤
      case 69:  draw_ttxt(-3, 3, color2, color1); break; // ◥
    }
    advance_cursor(1);
    return SUCCESS;
  } 
    
  // Hand-coded to fall back to mapped version of geometric shapes
  return handle_unicode_mapping_table(3, 10, c);
}


#endif //SOFTFONTS_H
