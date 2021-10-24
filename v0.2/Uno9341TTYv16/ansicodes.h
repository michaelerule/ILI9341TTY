#ifndef ANSICODES_H
#define ANSICODES_H

// ASCII codes
//#define NULL             (0)
#define START_OF_HEADING (uint8_t)(1)  
#define START_OF_TEXT    (uint8_t)(2)  
#define END_OF_TEXT      (uint8_t)(3)
#define END_TRANSMISSION (uint8_t)(4)
#define END_OF_FILE      (uint8_t)(4)
#define ENQUIRY          (uint8_t)(5)
#define ACKNOWLEDGEMENT  (uint8_t)(6)
#define BELL             (uint8_t)(7)
#define BACKSPACE        (uint8_t)(8)
#define HORIZONTAL_TAB   (uint8_t)(9)
#define NEWLINE          (uint8_t)(10)
#define VERTICAL_TAB     (uint8_t)(11)
#define FORM_FEED        (uint8_t)(12)
#define CARRIAGE_RETURN  (uint8_t)(13)
#define SHIFT_OUT        (uint8_t)(14)
#define SHIFT_IN         (uint8_t)(15)
#define DATALINE_ESCAPE  (uint8_t)(16)
#define XON              (uint8_t)(17)
#define DEVICE_CONTROL2  (uint8_t)(18) 
#define XOFF             (uint8_t)(19)
#define DEVICE_CONTROL4  (uint8_t)(20)
#define NEGATIVE_ACK     (uint8_t)(21)
#define SYNCHRONOUS_IDLE (uint8_t)(22)
#define END_TRANS_BLOCK  (uint8_t)(23) 
#define CANCEL           (uint8_t)(24)
#define END_MEDIUM       (uint8_t)(25)
#define SUBSTITUTE       (uint8_t)(26)
#define ESCAPE           (uint8_t)(27)
#define FILE_SEPARATOR   (uint8_t)(28)
#define GROUP_SEPARATOR  (uint8_t)(29)
#define RECORD_SEPARATOR (uint8_t)(30)
#define UNIT_SEPARATOR   (uint8_t)(31)
#define DELETE           (uint8_t)(127)
#define CSI              (uint8_t)(155)

// Aliases from gnome terminal
#define CTL_A START_OF_HEADING
#define CTL_B START_OF_TEXT
#define CTL_C END_OF_TEXT
#define CTL_D END_TRANSMISSION
#define CTL_E ENQUIRY
#define CTL_F ACKNOWLEDGEMENT
#define CTL_G BELL
#define CTL_H BACKSPACE
#define CTL_I HORIZONTAL_TAB
#define CTL_J NEWLINE
#define CTL_K VERTICAL_TAB
#define CTL_L FORM_FEED
#define CTL_M CARRIAGE_RETURN
#define CTL_N SHIFT_OUT
#define CTL_O SHIFT_IN
#define CTL_P DATALINE_ESCAPE
#define CTL_Q DEVICE_CONTROL1
#define CTL_R DEVICE_CONTROL2
#define CTL_S DEVICE_CONTROL3
#define CTL_T DEVICE_CONTROL4
#define CTL_U NEGATIVE_ACK
#define CTL_V SYNCHRONOUS_IDLE
#define CTL_W END_TRANS_BLOCK
#define CTL_X CANCEL
#define CTL_Y END_MEDIUM
#define CTL_Z SUBSTITUTE
#define CTL_2 NULL
#define CTL_3 ESCAPE
#define CTL_4 FILE_SEPARATOR
#define CTL_5 GROUP_SEPARATOR
#define CTL_6 RECORD_SEPARATOR
#define CTL_7 UNIT_SEPARATOR
#define CTL_8 DELETE
#define NUMLOCK CTL_K

/*
The "pen" has internal state.
This can be set via commands of the form CSI n m, where n is: 
0 	Reset
1 	Bold
2 	Faint
22 	Normal intensity	
30–37 	Set foreground color 	
38 	Set foreground color; Next arguments are 5;n or 2;r;g;b
39 	Default foreground color
40–47 	Set background color 	
48 	Set background color; Next arguments are 5;n or 2;r;g;b
49 	Default background color
100–107 Set bright background color 

Extras that would be nice to implement
4 	Underline
7 	Invert
9 	Crossed-out
21 	Doubly underlined; or: not bold
24 	Not underlined
27 	Not inverted
29 	Not crossed out 	
53 	Overlined
55 	Not overlined
58 	Set underline color Not in standard; implemented in Kitty, VTE, mintty, and iTerm2.[30][31] Next arguments are 5;n or 2;r;g;b.
59 	Default underline color

Tricky to implement
5 	Slow blink
6 	Rapid blink
25 	Not blinking 	
3 	Italic/inverse/blink
10 	Default font 	
11–19 	Alternative fonts
20 	Fraktur (Gothic)
23 	Neither italic, nor blackletter 
51 	Framed 	Implemented as "emoji variation selector" in mintty.[34]
52 	Encircled
54 	Neither framed nor encircled 	
*/

#define FG_DEFAULT ((uint8_t)WHITE)
#define BG_DEFAULT ((uint8_t)BLACK)

#define NORMAL         (0)
#define INVERT         (1)
// Font weights
#define BOLD           (1)
#define FAINT          (2)
// Underline and overline modes
#define SINGLE         (1)
#define DOUBLE         (2)
#define STRIKE         (3)
// Blink rate
#define BLINK          (1)
#define FASTBLINK      (2)
// Encircling decorations (not currently used)
#define FRAMED         (1)
#define ENCIRCLED      (2)
// Super/subscripts
#define SUPERSCRIPT    (1)
#define SUBSCRIPT      (2)
// Font styles
#define ITALIC         (1)
#define FRAKTUR        (2)
#define OUTLINE        (3)
#define TABLET         (4)
// Character width (one or two columns)
#define HALFWIDTH      (0)
#define FULLWIDTH      (1)












#endif /*ANSICODES_H*/
