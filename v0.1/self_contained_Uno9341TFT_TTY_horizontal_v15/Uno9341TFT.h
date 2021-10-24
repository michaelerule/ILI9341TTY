#ifndef _Uno9341TFT_H
#define _Uno9341TFT_H

#define swap(a,b)    {uint16_t t=a;a=b;b=t;}
#define swapU8(a,b)  {uint8_t  t=a;a=b;b=t;}
#define swapU16(a,b) {uint16_t t=a;a=b;b=t;}

#include "Arduino.h"
#include "colors.h"
#include "registers.h"
#include "delays.h"
#include "TFT_macros.h"

#define RS_PIN 4
#define CS_PIN 3
#define CD_PIN 2
#define WR_PIN 1
#define RD_PIN 0
#define CONTROLPORT PORTC
#define READ_BYTE ((PIND & 0b11111100)|(PINB & 0b00000011))
#define WRITE_BUS(b)  {PORTB=PORTD=(b);}
#define setWriteDir() {DDRD=DDRB=~0;}
#define setReadDir()  {DDRD=DDRB=0;}

#define WRITE_ZERO {PORTB=PORTD=0;}

class Uno9341TFT {
 public:
  Uno9341TFT(); // Constructor
  void
    // System configuration
    begin(),
    setRegisters8(uint8_t *ptr,uint8_t n),
    setRegisters16(uint16_t *ptr,uint8_t n),
    set_low_color_mode(uint8_t ison),
    // Core drawing routines
    clockb(uint8_t len),
    flood(uint8_t color,uint32_t len),
    fillRect(uint8_t x,uint16_t y,uint8_t w,uint16_t h,uint8_t color),
    fillScreen(uint8_t color),
    drawPixel(uint8_t x,uint16_t y,uint8_t color),
    drawFastVLine(uint8_t x,uint16_t y,uint16_t h,uint8_t color),
    drawFastHLine(uint8_t x,uint16_t y,uint8_t w,uint8_t color),
    drawRect(uint8_t x,uint16_t y,uint8_t w,uint16_t h,uint8_t color),
    // Pixel-reading routines
    readPixels(uint8_t nread,uint8_t *buffer),
    invertFlood(uint8_t length),
    invertRect(uint8_t x,uint16_t y,uint8_t w,uint16_t h);
 private: void init();
};

#endif // _Uno9341TFT_H
