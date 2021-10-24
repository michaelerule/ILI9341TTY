#ifndef MYFONT_H
#define MYFONT_H
// This file is automatically generated, do not edit it,
// see ./prepare_fonts/README.md for more information. 


////////////////////////////////////////////////////////////////////////////////
// No need to pollute workspace with a proliferation of separate C and H files!
// 
// This header contains data. 
// To avoid multiple definitions, Include it in only one C file, (before the
// data in it is used).

#ifdef __AVR__
 #include <avr/io.h>
 #include <avr/pgmspace.h>
#elif defined(ESP8266)
 #include <pgmspace.h>
#else
 #define PROGMEM
#endif

#define BYTESPERCHAR_BOXDRAWING (9)
#define NBYTES_BOXDRAWING       (1440)
#define CHAR_W_PX_BOXDRAWING    (6)
#define CHAR_H_PX_BOXDRAWING    (12)
#define NCHARS_BOXDRAWING       (160)
static const uint8_t font_6x12_boxdrawing[NBYTES_BOXDRAWING] PROGMEM = {
  65,32,8,4,129,32,16,4,130,0,0,0,192,1,0,0,0,0,0,0,0,0,128,32,8,130,32,0,0,
  0,192,193,32,8,130,32,0,0,0,0,12,0,0,0,0,0,0,0,192,15,0,0,0,0,0,0,0,0,140,33,
  8,130,32,0,0,0,192,143,32,8,130,32,8,130,32,8,0,0,0,0,0,8,130,32,204,1,0,0,0,
  0,8,130,32,8,130,32,8,130,32,8,130,32,200,131,32,8,130,32,8,130,32,24,12,0,0,
  0,0,8,130,32,200,15,0,0,0,0,8,130,32,8,142,32,8,130,32,8,130,32,200,143,32,8,
  130,32,32,8,65,8,66,16,130,16,4,0,0,0,7,114,0,0,0,0,0,0,0,0,66,81,20,69,81,0,
  0,0,7,114,81,20,69,81,0,0,0,48,2,3,0,0,0,0,0,0,63,240,3,0,0,0,0,0,0,48,66,83,
  20,69,81,0,0,0,63,112,83,20,69,81,20,69,81,20,2,0,0,0,0,20,69,81,23,114,0,0,0,
  0,20,69,81,20,69,81,20,69,81,20,69,81,23,116,81,20,69,81,20,69,81,52,2,3,0,0,
  0,20,69,81,55,240,3,0,0,0,20,69,81,52,65,83,20,69,81,20,69,81,55,112,83,20,69,
  81,0,0,0,128,7,0,0,0,0,0,0,0,158,231,1,0,0,0,0,130,32,8,0,32,8,130,0,0,199,
  113,28,0,112,28,199,1,0,0,0,128,13,0,0,0,0,0,0,0,182,109,3,0,0,0,8,2,32,8,128,
  32,0,130,0,28,7,112,28,192,113,0,199,1,0,0,0,64,5,0,0,0,0,0,0,0,85,85,1,0,0,0,
  8,128,0,8,128,0,8,128,0,28,192,1,28,192,1,28,192,1,191,239,243,60,142,243,188,
  239,255,255,255,255,255,255,207,115,24,2,255,247,61,207,113,60,207,247,253,64,
  24,206,243,255,255,255,255,255,64,16,12,195,113,12,67,16,0,0,0,0,0,0,48,140,
  231,253,0,8,194,48,142,195,48,8,2,191,231,49,12,0,0,0,0,0,65,16,4,65,16,4,65,
  16,4,130,32,8,130,32,8,130,32,8,4,65,16,4,65,16,4,65,16,8,130,32,8,130,32,8,
  130,32,16,4,65,16,4,65,16,4,65,32,8,130,32,8,130,32,8,130,0,0,0,0,0,0,0,240,
  255,0,0,0,0,0,0,255,15,0,0,0,0,0,240,255,0,0,0,0,0,0,255,15,0,0,0,0,0,240,255,
  0,0,0,0,0,0,255,15,0,0,0,0,0,0,0,127,16,4,65,16,4,65,16,4,65,16,4,65,16,4,65,
  16,252,32,8,130,32,8,130,32,8,254,63,8,130,32,8,130,32,8,130,63,0,0,0,0,0,0,0,
  252,63,0,0,63,240,3,63,0,252,0,0,0,0,0,0,192,255,255,0,0,0,0,0,252,255,255,
  255,0,0,0,192,255,255,255,255,255,0,0,252,255,255,255,255,255,255,192,255,255,
  255,255,255,255,255,255,32,8,130,32,8,130,32,8,130,48,12,195,48,12,195,48,12,
  195,56,142,227,56,142,227,56,142,227,60,207,243,60,207,243,60,207,243,190,239,
  251,190,239,251,190,239,251,133,80,8,133,80,8,133,80,8,16,10,161,16,10,161,16,
  10,161,0,0,0,0,80,169,149,90,169,149,90,169,149,10,0,0,0,0,149,90,169,149,90,
  169,149,90,169,149,90,169,149,250,255,255,255,255,255,255,255,255,95,169,149,
  90,169,215,123,189,215,123,189,215,123,189,189,222,235,189,222,235,189,222,
  235,12,51,207,12,51,207,12,51,207,243,204,48,243,204,48,243,204,48,255,15,0,
  255,15,0,255,15,0,49,206,57,199,24,227,156,115,140,227,225,112,120,60,30,14,
  135,199,64,24,206,243,255,207,115,24,2,191,231,49,12,0,48,140,231,253,0,16,8,
  133,80,40,149,82,169,0,8,129,16,74,161,148,90,169,149,74,169,20,10,161,16,8,
  128,149,90,41,133,82,8,129,16,0,0,0,0,64,16,8,2,65,32,0,0,0,0,0,128,32,4,33,8,
  65,8,66,16,0,0,0,0,8,4,129,32,0,0,0,0,0,8,65,8,66,16,8,2,65,32,8,4,129,32,0,
  128,32,4,33,8,69,137,98,16,0,0,0,0,0,0,0,64,16,136,34,69,33,8,4,129,96,16,8,2,
  65,32,8,65,8,66,16,128,32,4,33,8,69,137,98,16,128,32,4,33,8,69,137,98,16,8,2,
  65,32,8,4,129,96,16,136,34,69,33,8,65,8,66,16,136,34,69,33,8,69,137,98,16,136,
  34,69,33,0,0,72,210,47,73,0,0,0,0,164,57,190,231,24,2,0,0,0,0,252,123,253,126,
  63,0,0,0,225,65,184,46,243,48,12,0,0,128,25,3,0,12,12,0,0,0,0,236,61,216,174,
  63,0,0,23,198,97,208,11,0,0,0,0,186,225,24,66,15,0,0,0,0,255,90,175,245,31,
  134,165,251,129,97,24,134,97,8,126,110,25,134,0,224,251,190,47,248,62,15,0,0,
  240,125,223,7,61,1,0,0,0,0,72,51,0,204,18,0,0,63,8,130,224,121,158,32,8,254,0,
  0,120,237,60,183,30,0,0,0,0,220,239,247,255,63,0,0,0,0,204,173,231,181,51,0,0,
  0,0,204,173,36,181,51,0,0,0,160,27,158,105,24,134,14,0,0,112,32,31,216,205,
  200,15,0,0,0,0,0,0,60,208,3,0,0,0,236,255,252,182,51,0,0,128,72,81,136,202,33,
  20,7,0,128,72,81,8,194,169,20,7,0,128,72,81,136,194,161,20,7,0,128,72,81,8,
  202,41,20,7,0,128,239,115,156,202,33,20,7,0,0,32,218,170,40,138,20,2,0,63,0,0,
  192,15,0,0,0,0,255,220,182,243,15,0,0,0,0,97,24,254,115,219,206,127,24,134,97,
  24,134,97,24,134,97,24,134,48,239,251,255,255,255,190,207,195,195,243,125,255,
  255,255,223,247,12,0,39,138,34,32,138,34,7,0,0,0,130,32,0,130,32,0,0,0,39,8,2,
  7,130,32,7,0,0,7,130,32,7,130,32,7,0,0,0,130,32,39,138,34,0,0,0,7,130,32,39,8,
  2,7,0,0,39,138,34,39,8,2,7,0,0,0,130,32,0,130,32,7,0,0,39,138,34,39,138,34,7,
  0,0,7,130,32,39,138,34,7,0,0,0,0,0,0,0,0,0,0,};

// Use this to unpack font data form BOXDRAWING into a 12x6 character
// Assuming a length-12 global array char_bitmap exists
/*
char_bitmap[ 0]= (charbytes[0]<<0) & 0b111111;
char_bitmap[ 1]=((charbytes[0]>>6) & 0b11   ) | ((charbytes[1] & 0b1111) << 2);
char_bitmap[ 2]=((charbytes[1]>>4) & 0b1111 ) | ((charbytes[2] & 0b11  ) << 4);
char_bitmap[ 3]= (charbytes[2]>>2) & 0b111111;
char_bitmap[ 4]= (charbytes[3]<<0) & 0b111111;
char_bitmap[ 5]=((charbytes[3]>>6) & 0b11   ) | ((charbytes[4] & 0b1111) << 2);
char_bitmap[ 6]=((charbytes[4]>>4) & 0b1111 ) | ((charbytes[5] & 0b11  ) << 4);
char_bitmap[ 7]= (charbytes[5]>>2) & 0b111111;
char_bitmap[ 8]= (charbytes[6]<<0) & 0b111111;
char_bitmap[ 9]=((charbytes[6]>>6) & 0b11   ) | ((charbytes[7] & 0b1111) << 2);
char_bitmap[10]=((charbytes[7]>>4) & 0b1111 ) | ((charbytes[8] & 0b11  ) << 4);
char_bitmap[11]= (charbytes[8]>>2) & 0b111111;
*/
#endif /*MYFONT_H*/