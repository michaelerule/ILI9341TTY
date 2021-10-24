
#include <avr/pgmspace.h>
#include "pins_arduino.h"
#include "wiring_private.h"
#include "Uno9341TFT.h"
#define TFTWIDTH  240
#define TFTHEIGHT 320

////////////////////////////////////////////////////////////////////////////
// System configuration
/** Constructor for shield (fixed LCD control lines) */
Uno9341TFT::Uno9341TFT(void) {
  pinMode(A3, OUTPUT); // Enable outputs
  pinMode(A2, OUTPUT);
  pinMode(A1, OUTPUT);
  pinMode(A0, OUTPUT);
  digitalWrite(A4, HIGH); // reset
  pinMode(A4, OUTPUT);
  init();
}
/** Initialization common to both shield & breakout configs */
void Uno9341TFT::init(void) {
  setWriteDir(); // Set up LCD data port(s) for WRITE operations
}
/** Save space by storing initialization commands in a table */
#define DELAY_CODE 0
#define NCOMMANDS (11*3+2*6)
PROGMEM const byte initialization_commands[NCOMMANDS] = {
  DELAY_CODE           , 255,
  DELAY_CODE           , 255,
  ILI9341_SOFTRESET    , 0x00, 0x00,
  DELAY_CODE           , 255,
  ILI9341_DISPLAYOFF   , 0x00, 0x00,
  ILI9341_POWERCONTROL1, 0x23, 0x00,
  ILI9341_POWERCONTROL2, 0x10, 0x00,
  ILI9341_VCOMCONTROL1 , 0x2B, 0x2B,
  ILI9341_VCOMCONTROL2 , 0xC0, 0x00,
  ILI9341_MEMCONTROL   , ILI9341_MADCTL_MY|ILI9341_MADCTL_BGR, 0x00,
  ILI9341_PIXELFORMAT  , 0x55, 0x00,
  ILI9341_FRAMECONTROL , 0x00, 0x1B,
  ILI9341_SLEEPOUT     , 0x00, 0x00,
  DELAY_CODE           , 255,
  ILI9341_DISPLAYON    , 0x00, 0x00,
  DELAY_CODE           , 255,
  DELAY_CODE           , 255};
/** Retrieve command from the `initialization_commands` list */
inline byte get_init_command(byte i) {
  return (byte)pgm_read_byte(&initialization_commands[i]);
}
/** Send a byte of data over the 8-bit serial bus to the TFT display driver */
void send_byte(byte byte) {
  WRITE_BUS(byte); CLOCK_DATA;
}
/** Initialize a new TFT display connection */
void Uno9341TFT::begin() {
  ALL_IDLE;
  RS_LOW;
  delay(200);
  RS_HIGH;
  for(byte i=0; i<4; i++) COMMAND(0);
  byte hi,lo,code;
  for (unsigned int i=0; i<NCOMMANDS;) {
    code = get_init_command(i++);
    hi   = get_init_command(i++);
    if (code==DELAY_CODE) delay(hi);
    else {
      COMMAND(code);
      send_byte(hi);
      if ((lo = get_init_command(i++))) {send_byte(lo); CLOCK_DATA;}
    }
  }
}

/** Control 3-bit color mode */ 
void Uno9341TFT::set_low_color_mode(byte ison) {
  COMMAND(ison?LOW_COLOR_MODE_ON:LOW_COLOR_MODE_OFF);
}

////////////////////////////////////////////////////////////////////////////
// Core drawing routines

/** Very fast way to flood up to 255 pixels. Elimenates loop overhead.
 */
void Uno9341TFT::clockb(byte len) {
  if (len&0b10000000) {CLOCK_128;}
  if (len&0b01000000) {CLOCK_64; }
  if (len&0b00100000) {CLOCK_32; }
  if (len&0b00010000) {CLOCK_16; }
  if (len&0b00001000) {CLOCK_8;  }
  if (len&0b00000100) {CLOCK_4;  }
  if (len&0b00000010) {CLOCK_2;  }
  if (len&0b00000001) {CLOCK_1;  }
}

/** Flood given `color` for `len` pixels. 
 * @param color 8-bit color code
 * @param len number of pixels to fill
 */
void Uno9341TFT::flood(byte color, uint32_t len) {
  START_PIXEL_DATA();
  WRITE_BUS(color);
  while (len>=256) {CLOCK_256; len-=256;} 
  clockb(len);
}
/** Fill rectangular region of screen.
 * @param x horizontal coordinate of start of rectangular regi on
 * @param y vertical coordinate of start of rectangular region
 * @param w width of rectangular region (assumes dimension<=240)
 * @param h height of rectangular region
 * @param color 8-bit 323 RBG color code
 */
void Uno9341TFT::fillRect(byte x1, unsigned int y1, byte w, unsigned int h, byte color) {
  byte x2=x1+w-1;
  SET_XY_RANGE(x1,x2,y1);
  flood(color, (uint32_t)w*(uint32_t)h);
}
/** Fill screen.
 * @param color 8-bit 323 RGB color code
 */
void Uno9341TFT::fillScreen(byte color) {
  fillRect(0,0,TFTWIDTH,TFTHEIGHT,color);
}
/** Write a single pixel.
 * @param x Pixel horizontal location
 * @param y Pixel vertical location
 * @param color 8-bit 323 RGB color code
 */
void Uno9341TFT::drawPixel(byte x, unsigned int y, byte color) {
  SET_XY_RANGE(x,x,y);
  START_PIXEL_DATA();
  WRITE_BUS(color);
  CLOCK_1;
}
/** Fill vertical line.
 * @param x Pixel horizontal location
 * @param y Pixel vertical location
 * @param color 8-bit 323 RGB color code
 */
void Uno9341TFT::drawFastVLine(byte x, unsigned int y, unsigned int length, byte color)
{
  SET_XY_RANGE(x,x,y);
  flood(color, length);
}
/** Fast horizontal line routine
 * @param x horizontal position of start of horizontal line
 * @param y vertical position of start of horizontal line
 * @param length width of horizontal line
 * @param color 8-bit 323 RGB color code
 */
void Uno9341TFT::drawFastHLine(byte x, unsigned int y, byte w, byte color){
  SET_XY_RANGE(x,TFTWIDTH,y);
  flood(color,w);
}
/** Fast rectangle ouline using hline/vline
 * @param x horizontal coordinate of start of rectangular regi on
 * @param y vertical coordinate of start of rectangular region
 * @param w width of rectangular region (assumes dimension<=240)
 * @param h height of rectangular region
 * @param color 8-bit 323 RGB color code
 */
void Uno9341TFT::drawRect(byte x, unsigned int y, byte w, unsigned int h, byte c) {
  drawFastHLine(x, y, w, c);
  drawFastHLine(x, y+h-1, w, c);
  drawFastVLine(x, y, h, c);
  drawFastVLine(x+w-1, y, h, c);
}
////////////////////////////////////////////////////////////////////////////
// Pixel-reading routines
/** Read pixels back from display
 * @param nread  number of pixels to read (less than 256)
 * @param buffer buffer to store results
 */
void Uno9341TFT::readPixels(byte nread, byte *buffer) {
  COMMAND(BEGIN_READ_DATA);
  READY_READ;
  SEND_DATA;
  DDRD = DDRB = 0; // switch to input mode (use as a delay)
  READY_READ;
  nread--;
  byte i=0;
  for (; i<nread; i++) {
    byte b= READ_BYTE;  // Read low byte of pixel data
    SEND_DATA; READY_READ; // Skip hi byte (set hi=lo~8-bit RRGGGBB)
    SEND_DATA;             // Advance to next pixel location
    buffer[i]=b;           // Assign to buffer here to add delay
    READY_READ;            // Prepare to read next pixel
  }
  DELAY1;
  buffer[i]=READ_BYTE;
  DDRD = DDRB = ~0; // switch to output mode
}
/** Flood routine which x-ors color data
 * @param length number of pixels to x-or (<256)
 **/
void Uno9341TFT::invertFlood(byte length) {
  byte colors[length];
  readPixels(length,colors);
  START_PIXEL_DATA();
  for(byte i=0; i<length; i++) {
    WRITE_BUS(~colors[i]);
    CLOCK_1;
  }
}
/* Draw a rectangle in x-or mode. This could be better optimized! 
 * At present it is fast for short, wide rectangles. (tall, thin
 * in landscape mode);
 *
 * @param x horizontal coordinate of start of rectangular regi on
 * @param y vertical coordinate of start of rectangular region
 * @param w width of rectangular region (assumes dimension <=240)
 * @param h height of rectangular region
 * @param color 8-bit 323 RBG color code
 */
void Uno9341TFT::invertRect(byte x, unsigned int y, byte w, unsigned int h) {
  SET_XY_RANGE(x,(x+w-1),y);
  for (unsigned int i=0; i<h; i++) {
    SET_Y_LOCATION(i+y);
    invertFlood(w);
  }
}


