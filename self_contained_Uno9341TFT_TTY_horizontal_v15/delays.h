// Inline assembly commands for inserting very short delays.
// Reading data form the 9341 in particular requires a certain delay
// between when the read command is sent and when the data becomes
// available on the bus line. These delays are used as "shims" to get
// the timing right. They are currently set for a 16MHz clock, and 
// modificatios of the AtMega clock rate will likely required adjusting
// the inline delays used for reading data. ( I'm looking at use over-
// clockers). 
// 
// Pixel read operations require a minimum 400 nS delay from RD_ACTIVE
// to polling the input pins.  At 16 MHz, one machine cycle is 62.5 nS.
// RJMPs are equivalent to two NOPs each, 
// NOP burns one cycle
#define DELAY7        \
  asm volatile(       \
    "rjmp .+0" "\n\t" \
    "rjmp .+0" "\n\t" \
    "rjmp .+0" "\n\t" \
    "nop"      "\n"   \
    ::);

#define DELAY3      \
  asm volatile(       \
    "rjmp .+0" "\n\t" \
    "nop"      "\n"   \
    ::);
#define DELAY2      \
  asm volatile(       \
    "rjmp .+0" "\n\t" \
    "nop"      "\n"   \
    ::);
#define DELAY1      \
  asm volatile(       \
    "rjmp .+0" "\n\t" \
    "nop"      "\n"   \
    ::);
