
//////////////////////////////////////////////////////////////////////////
// Platform-independent IO macros

#define RS_FLAG ((uint8_t)1<<RS_PIN)
#define CS_FLAG ((uint8_t)1<<CS_PIN)
#define CD_FLAG ((uint8_t)1<<CD_PIN)
#define WR_FLAG ((uint8_t)1<<WR_PIN)
#define RD_FLAG ((uint8_t)1<<RD_PIN)

#define CONTROL_MASK (RS_FLAG|CS_FLAG|CD_FLAG|WR_FLAG|RD_FLAG)
#define TFTDEFAULT (~CONTROL_MASK|RS_FLAG)

#define READY_COMMAND     CONTROLPORT=(TFTDEFAULT|RD_FLAG)
#define SEND_COMMAND      CONTROLPORT=(TFTDEFAULT|RD_FLAG|WR_FLAG)
#define READY_DATA        CONTROLPORT=(TFTDEFAULT|CD_FLAG|RD_FLAG)
#define READY_READ        CONTROLPORT=(TFTDEFAULT|CD_FLAG|WR_FLAG)
#define SEND_DATA         CONTROLPORT=(TFTDEFAULT|CD_FLAG|WR_FLAG|RD_FLAG)
#define REQUEST_READ      CONTROLPORT=(TFTDEFAULT|WR_FLAG)

#define ALL_IDLE   CONTROLPORT = TFTDEFAULT|CS_FLAG

#define CS_IDLE    CONTROLPORT |=  CS_FLAG
#define CS_ACTIVE  CONTROLPORT &= ~CS_FLAG
#define RD_ACTIVE  CONTROLPORT &= ~RD_FLAG
#define RD_IDLE    CONTROLPORT |=  RD_FLAG
#define WR_ACTIVE  CONTROLPORT &= ~WR_FLAG
#define WR_IDLE    CONTROLPORT |=  WR_FLAG
#define RS_LOW     CONTROLPORT &= ~WR_FLAG
#define RS_HIGH    CONTROLPORT |=  WR_FLAG
#define CD_COMMAND CONTROLPORT &= ~CD_FLAG
#define CD_DATA    CONTROLPORT |=  CD_FLAG
   
// Data write strobe, ~2 instructions and always inline
#define WR_STROBE {WR_ACTIVE;WR_IDLE;}
#define write8(d) {WRITE_BUS(d);WR_STROBE;}
#define read8(result) {RD_ACTIVE;DELAY7;result = READ_BYTE;RD_IDLE;}
#define CLOCK_DATA {READY_DATA;SEND_DATA;}
#define COMMAND(CMD) {WRITE_BUS(CMD);READY_COMMAND;SEND_COMMAND;}
#define START_PIXEL_DATA() {COMMAND(BEGIN_PIXEL_DATA);}
#define SEND_LOW(lo) {WRITE_ZERO;CLOCK_DATA;WRITE_BUS(lo);CLOCK_DATA;}
#define SEND_PAIR(hi,lo) {WRITE_BUS(hi);CLOCK_DATA;WRITE_BUS(lo);CLOCK_DATA;}
#define SEND_PIXEL(color) {SEND_PAIR(color>>8,color);}

// For loop unrolling in the fast color flood routine. 
// The number referes to the number of pixels to send.
// Since the high and low bytes of "fast" colors are the same, we send two
// clock pulses per pixel.
#define CLOCK_1   {CLOCK_DATA; CLOCK_DATA;};
#define CLOCK_2   {CLOCK_1   CLOCK_1};
#define CLOCK_4   {CLOCK_2   CLOCK_2};
#define CLOCK_8   {CLOCK_4   CLOCK_4};
#define CLOCK_16  {CLOCK_8   CLOCK_8};
#define CLOCK_32  {CLOCK_16  CLOCK_16};
#define CLOCK_64  {CLOCK_32  CLOCK_32};
#define CLOCK_128 {CLOCK_64  CLOCK_64};
#define CLOCK_256 {CLOCK_128 CLOCK_128};

// If N is a #define then hopefully this should compile to the correct number of clock pulses
//#define CLOCK_N(n) {if (n&1) CLOCK_1; if (n&2) CLOCK_2; if (n&4) CLOCK_4; if (n&8) CLOCK_8; if (n&16) CLOCK_16; if (n&32) CLOCK_32; if (n&64) CLOCK_64; if (n&128) CLOCK_128;}

//////////////////////////////////////////////////////////////////////////
// Configure drawing region

#define ZERO_XY() {\
  COMMAND(SET_COLUMN_ADDRESS_WINDOW);\
  WRITE_ZERO;\
  CLOCK_DATA;\
  CLOCK_DATA;\
  COMMAND(SET_ROW_ADDRESS_WINDOW);\
  WRITE_ZERO;\
  CLOCK_DATA;\
  CLOCK_DATA;\
}

// Set the X location 
// Because x in 0..239, top byte is always 0
#define SET_X_LOCATION(x) {COMMAND(SET_COLUMN_ADDRESS_WINDOW);SEND_LOW(x);}

// Set the Y location
#define SET_Y_LOCATION(y) {COMMAND(SET_ROW_ADDRESS_WINDOW);SEND_PAIR((y)>>8,((uint8_t)(y)));}

// Set both X and Y location
#define SET_XY_LOCATION(x,y) {SET_X_LOCATION(x);SET_Y_LOCATION(y);}

// Set X range
#define SET_X_RANGE(x1,x2) {COMMAND(SET_COLUMN_ADDRESS_WINDOW);SEND_LOW(x1);SEND_LOW(x2);}

// Set Y range
#define SET_Y_RANGE(y1,y2) {COMMAND(SET_ROW_ADDRESS_WINDOW);SEND_PAIR((y1)>>8,((uint8_t)(y1)));SEND_PAIR((y2)>>8,((uint8_t)(y2)));}

// Set X range and Y location; Assumes upper Y limit is always the screen height
#define SET_XY_RANGE(x1,x2,y) {SET_X_RANGE(x1,x2);SET_Y_LOCATION(y);}

// TODO: these constants are multiply defined, clear this up
#define XWIDTH  (240)
#define YHEIGHT (320)
#define MAXX    (XWIDTH-1)
#define MAXY    (YHEIGHT-1)

// Sets X range to (0,239)
#define RESET_X_RANGE() {\
  COMMAND(SET_COLUMN_ADDRESS_WINDOW);\
  WRITE_ZERO; CLOCK_DATA; CLOCK_DATA;\
  CLOCK_DATA; WRITE_BUS(MAXX); CLOCK_DATA;\
}

// Sets Y range to (0,319)
#define RESET_Y_RANGE() {\
  COMMAND(SET_ROW_ADDRESS_WINDOW);\
  WRITE_ZERO; CLOCK_DATA; CLOCK_DATA;\
  WRITE_BUS(MAXY>>8); CLOCK_DATA;\
  WRITE_BUS((uint8_t)MAXY); CLOCK_DATA;\
}

#define RESET_XY_RANGE() {RESET_X_RANGE(); RESET_Y_RANGE();}

/*
Sets the LCD address window (and address counter, on 932X).
Relevant to rect/screen fills and H/V lines.  Input coordinates are
assumed pre-sorted (e.g. x2 >= x1).
This does not set the upper bounds for the row information. This is left
at the initialization value of 319. There is no reason to ever change this
register. 
*/
#define SET_WINDOW(x1,y1,x2,y2) {SET_XY_RANGE(x1,x2,y1);}

/*
In order to save a few register writes on each pixel drawn, the lower-right
corner of the address window is reset after most fill operations, so that 
drawPixel only needs to change the upper left each time.
The row range is set to 0..239
The col range is set to 0..Current
Transmission of the end of the column range command is ommitted, as this
should be set to 319 during initialization and is never changed by the
driver code. As long as no other code sends data afterwards, this register
will remain set to its original value. This driver does not send data
without issuing a command first, so this works. However, it could interact
poorly with user code if the chip select line for the touch screen is not
disabled prior to performing IO operations on PORTC. 
*/
#define SET_LR(void) {RESET_X_RANGE();ZERO_Y();}

// Start reading pixel data
#define START_READING() {COMMAND(BEGIN_READ_DATA);setReadDir();READY_READ;SEND_DATA;DELAY1;READY_READ;DELAY1;}
// Finish reading pixel data
#define STOP_READING() {setWriteDir();}
