
// Helper routines for transformations

// Flip rows in character bitmap
#define FLIP_CBM(a,b) {byte temp=char_bitmap[a]; char_bitmap[a]=char_bitmap[b]; char_bitmap[b]=temp;}

// Mirror horizontally for odd-width characters
void mirror_horizontal_5() {
  for (byte i=0; i<CH; i++) {
    // Specialized for 6-px wide fonts
    //byte b = char_bitmap[i] & 0b11111;
    // 12345 -> 1-3254
    //b = ((0b010101&b)<<1)|((0b101010&b)>>1);
    // 1-3254 -> 54321
    //b = ((0b00000011&b)<<3)|((0b00001100&b)>>1)|((0b00100000&b)>>6);
    //char_bitmap[i] = b;
    
    byte b = char_bitmap[i] & 0b111110;
    // 12345X -> 34512X
    b = ((b&(1<<1))<<4) |
        ((b&(1<<2))<<2) |
        ((b&(1<<3))<<0) |
        ((b&(1<<4))>>2) |
        ((b&(1<<5))>>4);
    char_bitmap[i] = b;
  }
}

// Mirror horizontally for even-width charactes
void mirror_horizontal_6() {
  for (byte i=0; i<CH; i++) {
    // Specialized for 6-px wide fonts
    byte b = char_bitmap[i] & 0b111111;
    // 123456 -> 456123
    b = ((0b000111&b)<<3)|((0b111000&b)>>3);
    // 456123 -> 654321
    b = ((0b100100&b)>>2)|((0b001001&b)<<2)|(0b010010&b);
    char_bitmap[i] = b;
  }
}

// Flip vertically for upper-case letters
void mirror_vertical() {
  //for (byte i=0; i<CH/2; i++) FLIP_CBM(i,CH-1-i);
  // 01 2345678 9AB 
  // A9 8765432 10X
  FLIP_CBM(0,10);
  FLIP_CBM(1,9);
  FLIP_CBM(2,8);
  FLIP_CBM(3,7);
  FLIP_CBM(4,6);
  char_bitmap[11]=0;
}

// Flip lower-case letter vertically
void mirror_vertical_miniscule() {
    // Specialized for 12x6 fonts
    // 01 23456 789AB
    // 87 65432 10xxx
    FLIP_CBM(0,8);
    FLIP_CBM(1,7);
    FLIP_CBM(2,6);
    FLIP_CBM(3,5);
    char_bitmap[9]=0;
    char_bitmap[10]=0;
    char_bitmap[11]=0;
}
