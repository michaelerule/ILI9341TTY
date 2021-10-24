#define color565(r, g ,b) ((((r)&0xF8)<<8)|(((g)&0xFC)<<3)|((b)>>3))

// Assign human-readable names to some common 16-bit color values:
// Using values with identical high and low bytes gives faster
// Rendering of filled regions


// Colors packed as (rrr bb ggg) 8-bit integers

// Mask drawing allows erasing after draw (we don't use it in the terminal)
#define MASK   ~0b11110111

// Dark colors
#define BLACK     0b00000000
#define DKRED     0b10000000
#define DKGREEN   0b00000100
#define DKYELLOW  0b01100011
#define DKBLUE    0b00010000
#define DKMAGENTA 0b10010000
#define DKCYAN    0b00010100
#define LTGREY    0b10010100

// Bright colors
#define GREY    0b01001010
#define RED     0b11100000
#define GREEN   0b00000111
#define YELLOW  0b11100111
#define BLUE    0b00111001
#define MAGENTA 0b11111000
#define CYAN    0b00011111
#define WHITE   0b11111111

// 16-color pallet, ANSI terminal
const uint8_t color_cycle[16] = {
  BLACK,
  DKRED,
  DKGREEN,
  DKYELLOW,
  DKBLUE,
  DKMAGENTA,
  DKCYAN,
  LTGREY,
  GREY,
  RED,
  GREEN,
  YELLOW,
  BLUE,
  MAGENTA,
  CYAN,
  WHITE,
};

// Other colors
#define PURPLE  0b01110000
#define LIME    0b01100111
#define ORANGE  0b11100100

// Masks for each channel, for the "fadecolor" function in "textgrpahics.h"
#define RMASK (0b11100000)
#define BMASK (0b00011000)
#define GMASK (0b00000111)
#define RGMASK (RMASK|GMASK)
