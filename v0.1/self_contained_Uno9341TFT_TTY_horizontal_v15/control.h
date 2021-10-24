#ifndef CONTROL_H
#define CONTROL_H

////////////////////////////////////////////////////////////////////////////////
// Control sequence parsing
/*
Class Fe:    ESC + [0x40-0x5F ]
Class CSI:  (ESC + '[' | CSI) + [0x30-0x3F]* + [0x20-0x2F]* + [0x40-0x7E]
Class nF:    ESC + [0x20-0x2F] + [0x20-0x2F]* + [0x30-0x7E]
Class Fp:    ESC + [0x30-0x3F]

Sequences containing the parameter bytes <=>? 
or the final bytes 0x70–0x7E (p–z{|}~) are private. 

ESC NOP\]X^_ not supported

We process CSI escape sequences by reading the escape sequence bytes and
checking that htey are a valid ANSI code. We then parse the parameters of the
escape sequence into another buffer. These constants set the maximum number of
bytes in the escape sequence parameters (and maximum number of parameters)
*/

#define CSMAXBYTES (24)
#define CSBUFFERLEN (CSMAXBYTES+2)

/** Read numeric parameters from a CSI code.
 *  "s" must be null-terminated.
 */
int read_csi_arguments(const byte *s, uint16_t *cs_parse_buff) {
  // Treat empty buffer as special case
  if (s[0]==0) return 0;
  int n=0;
  int nread=0;
  for (int i=0; i<CSMAXBYTES+2; i++) {
    byte c = s[i];
    // If digit => accumulate number
    if (c>='0' && c<='9') {
      n=n*10+(c-'0');
    }
    // else, terminator or separator => done with this number
    // store number, return if done, else continue to next number
    else if (c==';'||c==0) {
      cs_parse_buff[nread++]=n;
      if (c==0) return nread;
      n=0;
    }
    else return -1; // Encountered unexpected data
  }
  return -2; // Buffer overflow
}

/** Send back decimal formatted byte
 *  Used to respond to requests for cursor position
 */
void serial_write_decimal(byte value) {
  Serial.write('0'+value/100); 
  value%=100;
  Serial.write('0'+value/10); 
  value%=10;
  Serial.write('0'+value);
} 

/** Set color register based on CSI code for 256/12-bit modes
 */
int set_color_csi(byte *color_register, const uint16_t *cs_parse_buff, int nread) {
  int r,g,b;
  if (nread<3) return FAIL;
  if (cs_parse_buff[1]==5) {
    // Color as index into 256-color pallet
    if (!(nread==3)) return FAIL;
    uint16_t n = cs_parse_buff[2];
    if (n>255) return FAIL;
    if (n<16) { // 16-color pallet
      *color_register = color_cycle[n];
      // Return number of parameters consumed so we can continue parsing 
      // additional parameters and codes, if present. 
      return SUCCESS;
    } 
    if (n<232) { // 6,6,6 cube
      n -= 16;
      b = ((n%6)*255)/5;
      g = (((n/6)%6)*255)/5;
      r = (((n/36)%6)*255)/5;
    }
    else r=g=b=((n-232)*255)/23; // greyscale
  } else if (cs_parse_buff[1]==2) {
    // Color as RGB tuple
    if (!(nread==5)) return FAIL;
    r = cs_parse_buff[2];
    g = cs_parse_buff[3];
    b = cs_parse_buff[4];
  }
  else return FAIL;
  // Format is RRR BB GGG
  if (r>255) return FAIL;
  if (g>255) return FAIL;
  if (b>255) return FAIL;
  *color_register = (byte)(
    (r&0b11100000)|((b>>3)&0b00011000)|((g>>5)&0b00000111)
  ); 
  return SUCCESS;
}
 
/** Parse and respond to escape sequence
 *  SCI compliant escape codes:
 *  ESC [ is followed by any number (including none) of "parameter bytes" in the range 0x30–0x3F (ASCII 0–9:;<=>?), 
 *  then by any number of "intermediate bytes" in the range 0x20–0x2F (ASCII space and !"#$%&'()*+,-./),
 *  then finally by a single "final byte" in the range 0x40–0x7E (ASCII @A–Z[\]^_`a–z{|}~)
 */
int parse_CSI_sequence() 
{  
  // buffers to hold bytes from control sequences as we receive and parse them
  // (and variables to keep track of how many bytes read)
  byte  cs_param_buff[CSBUFFERLEN]; // store parameter bytes from CSI code
  //byte  cs_inter_buff[CSBUFFERLEN]; // store intermediate bytes ""
  uint16_t cs_parse_buff[CSBUFFERLEN]; // store parsed integer arguments, semicolon separated, for CSI
  byte  n_cs_param_bytes = 0;
  //byte  n_cs_inter_bytes = 0;
  byte  cs_final_byte    = 0;

  // Get parameter bytes 
  byte i;
  byte inByte = blocking_read();
  for (i=0; i<CSMAXBYTES; i++) {
    if (!(0x30<=inByte && inByte<=0x3f)) break;
    cs_param_buff[i] = inByte;
    inByte = blocking_read();
  }
  if (i>=CSMAXBYTES) return FAIL; // buffer overflow (bad/unsupported code)
  n_cs_param_bytes = i;
  cs_param_buff[i] = 0; // Null terminate, important!
  
  // Get intermediate bytes
  for (i=0; i<CSMAXBYTES; i++) {
    if (!(0x20<=inByte && inByte<=0x2f)) break;
    //cs_inter_buff[i] = inByte;
    inByte = blocking_read();
  }
  if (i>=CSMAXBYTES) return FAIL; // buffer overflow (bad/unsupported code)
  //n_cs_inter_bytes = i;
  //cs_inter_buff[i] = 0; // Null terminate, important!
  
  if (!(0x40<=inByte && inByte<=0x7E)) return FAIL; // bad final byte
  cs_final_byte = inByte;
  
  // Show/hide cursor [?25h [?2fl are handled as a special cases 
  if (n_cs_param_bytes>0 && cs_param_buff[0]=='?') {
    // Private use sequences, get numeric arguments if any
    int nread = read_csi_arguments(&cs_param_buff[1], cs_parse_buff);
    if (nread!=1 || cs_parse_buff[0]!=25) return FAIL;
    switch (cs_final_byte) {
      case 'h': show_cursor(); break;
      case 'l': hide_cursor(); break;
      default: return FAIL;
    }
  }
  
  // For the remaining codes, we assume they start with a number
  if (n_cs_param_bytes>0 && !('0'<=cs_param_buff[0] && cs_param_buff[0]>='0')) return FAIL;
  
  // Parse parameters (we expect ; separated list of positive ints)
  int nread = read_csi_arguments(cs_param_buff, cs_parse_buff);
  if (nread<0) return FAIL;
    
  // Pring output for debugging? 
  /*
  print("[");
  cs_param_buff[n_cs_param_bytes]   = cs_final_byte;
  cs_param_buff[n_cs_param_bytes+1] = 0;
  print((char *)cs_param_buff);
  printch('(');
  printch(cs_param_buff[0]);
  printch(')');
  printch('(');
  printch('0'+min(9,max(0,nread)));
  printch(')');
  for (int j=0; j<nread; j++) 
  {
    uint16_t q = cs_parse_buff[j];
    for (int k=0; k<3; k++) 
    {
        printch('0'+q%10);
        q /= 10;
    }
    printch(';');
  }*/

  
  // If the final byte is ABCDEFG, we should expect an arrow navigation 
  // command with one or zero numerical arguments
  if ('A'<=cs_final_byte && cs_final_byte<='G') {
    int16_t n = nread? cs_parse_buff[0] : 1;
    cstamp();  
    switch (cs_final_byte) {
      case 'F': // Up, start of line
        col=0; 
      case 'A': // Up
        n   = min(TR-1,n);
        row = min(TR-1,row+n);
        break;
      case 'E': // Down, start of line
        col=0; 
      case 'B': // Down 
        n   = min(TR-1,n);
        row = n>row? 0 : row-n;
        break;
      case 'C': // Right
        n   = min(TC-1,n);
        col = min(TC-1,col+n);
        break;
      case 'D': // Left
        n   = min(TC-1,n);
        col = n>col? 0 : col-n;
        break;
      case 'G': // Jump to column n
        col = min(TC,n)-1;
        break;
      default: // Should never reach here
        cstamp();  
        return FAIL; 
    }
    cstamp();
    return SUCCESS;
  }
  
  // If the final byte is H or f, we should expect a cursor positioning
  // command with up to two arguments.
  else if (cs_final_byte=='H' || cs_final_byte=='f') { 
    // "Cursor position" and "Horizontal Vertical Position" (H,f)
    cstamp();  
    row = nread<1? TR-1
      : max(0,min(TR-1,TR-max(1,cs_parse_buff[0])));
    col = nread<2? 0 : ((byte)max(1,min(TC,cs_parse_buff[1]))-1);
    cstamp();  
    return SUCCESS; 
  }
  
  // If the final byte is m, expect a sequence of Select Graphic Rendition (SGR)
  // parameters, separated by semicolons. These semicolon-delimited arguments
  // have already been parsed by "read_csi_arguments", and are stored in 
  // the buffer "cs_parse_buff". The variable nread describes how many
  // parameters were read. We need to continue reading commands until the 
  // sequence is exhausted. 
  // TODO: I need to adjust the color-parsing code to play nicely with this.
  // 
  else if (cs_final_byte=='m') {
    // There should always be at least one argument
    if (nread<1) return FAIL;
    
    for (byte param_i=0; param_i<nread; param_i++) {
      
      byte code = (byte)cs_parse_buff[param_i];
      // Parameters should be <256
      if (code>255) return FAIL;
      
      // Keep this as a consecutive order with the hope that the compiler
      // converts it to a fast jump table.
      switch (code) {
        case 0 : reset_text_attributes();      break; //Reset all text attributes
        case 1 : font_weight    = BOLD;        break; //Bold intensity
        case 2 : font_weight    = FAINT;       break; //Faint intensity
        case 3 : font_mode      = ITALIC;      break; //Italic style
        case 4 : underline_mode = SINGLE;      break; //Underline
        case 5 : blink_mode     = BLINK;       break; //Slow blink
        case 6 : blink_mode     = FASTBLINK;   break; //Rapid blink
        case 7 : invert         = INVERT;      break; //Invert
        case 8 :                               break; //Conceal (not supported)
        case 9 : strike_mode    = STRIKE;      break; //Crossed-out
        case 10: font_mode      = NORMAL;      break; //Default font mode; interpreted here as same as code 23
        case 11: font_mode      = OUTLINE;     break; //Alt font 1 will try to approximate blackboard bold
        case 12: font_mode      = TABLET;      break; //Encase letters in rounded rectangle
        case 13: font_mode      = NORMAL;      break; //Other alternative fonts are not defined
        case 14: font_mode      = NORMAL;      break; // ... could be implemented as weird variants on bold
        case 15: font_mode      = NORMAL;      break; // ... unsupported font
        case 16: font_mode      = NORMAL;      break; // ... unsupported font
        case 17: font_mode      = NORMAL;      break; // ... unsupported font
        case 18: font_mode      = NORMAL;      break; // ... unsupported font
        case 19: font_mode      = NORMAL;      break; // ... unsupported font
        case 20: font_mode      = FRAKTUR;     break; //Fraktur style (implemented as "very bold")
        case 21: underline_mode = DOUBLE;      break; //Doube underlined
        case 22: font_weight    = NORMAL;      break; //Normal intensity
        case 23: font_mode      = NORMAL;      break; //Remove italic or fraktur style
        case 24: underline_mode = NORMAL;      break; //Not underlined
        case 25: blink_mode     = NORMAL;      break; //Not blinking 	
        case 26:                               break; //Proportional spacing; not supported
        case 27: invert         = NORMAL;      break; //Not inverted
        case 28:                               break; //Reveal (not concealed); not supported
        case 29: strike_mode    = NORMAL;      break; //Not crossed out 
        case 30: fg = color_cycle[8];          break; //Foreground colors
        case 31: fg = color_cycle[9];          break;
        case 32: fg = color_cycle[10];         break;
        case 33: fg = color_cycle[11];         break;
        case 34: fg = color_cycle[12];         break;
        case 35: fg = color_cycle[13];         break;
        case 36: fg = color_cycle[14];         break;
        case 37: fg = color_cycle[15];         break;
        case 38://Set foreground color; Next arguments are 5;n or 2;r;g;b
          return set_color_csi(&fg,&cs_parse_buff[param_i],nread-param_i); // TODO
        case 39: fg             = FG_DEFAULT;  break; //Default foreground color
        case 40: bg = color_cycle[0];          break; //Background colors
        case 41: bg = color_cycle[1];          break; //Background colors
        case 42: bg = color_cycle[2];          break; //Background colors
        case 43: bg = color_cycle[3];          break; //Background colors
        case 44: bg = color_cycle[4];          break; //Background colors
        case 45: bg = color_cycle[5];          break; //Background colors
        case 46: bg = color_cycle[6];          break; //Background colors
        case 47: bg = color_cycle[7];          break; //Background colors
        case 48://Set background color; Next arguments are 5;n or 2;r;g;b
          return set_color_csi(&bg,&cs_parse_buff[param_i],nread-param_i); // TODO
        case 49: bg             = BG_DEFAULT;  break; //Default background color
        case 50:                               break; //Disable proportional spacing; not supported
        case 51: frame_mode     = FRAMED;      break; //Supposed to be a "framed" effect
        case 52: frame_mode     = ENCIRCLED;   break; //Supposed to be an "encircled" effect
        case 53: overline_mode  = SINGLE;      break; //Overlined
        case 54: frame_mode     = NORMAL;      break; //Clear framed/circled effect
        case 55: overline_mode  = NORMAL;      break; //Not overlined 
        case 56: break; // Available for private use?
        case 57: break; // Available for private use?
        case 58://Set underline color. Next arguments are 5;n or 2;r;g;b.
          return set_color_csi(&ul,&cs_parse_buff[param_i],nread-param_i); // TODO
        case 59: ul             = FG_DEFAULT;  break; //Default underline color
        case 60: underline_mode = SINGLE;      break; //Ideogram line mapped to underline
        case 61: underline_mode = DOUBLE;      break; //Ideogram double line mapped to double underline
        case 62: overline_mode  = SINGLE;      break; //Ideogram overline mapped to overline
        case 63: overline_mode  = DOUBLE;      break; //Ideogram double overline as double overline
        case 64: break; //Ideogram stress marking not supported
        case 65: //"No ideogram attributes" mapped to "not overlined or underlined" 
          underline_mode = overline_mode = NORMAL; break; 
        case 66: break; // Available for private use?
        case 67: break; // Available for private use?
        case 68: break; // Available for private use?
        case 69: break; // Available for private use?
        case 70: break; // Available for private use?
        case 71: break; // Available for private use?
        case 72: break; // Available for private use?
        case 73: script_mode    = SUPERSCRIPT; break; //Superscript mode (not yet implemented)
        case 74: script_mode    = SUBSCRIPT;   break; //Subscript mode (not yet implemented)
        case 75: script_mode    = NORMAL;      break; //Ecit sub/superscript mode
        default:
          //90–97 Set bright foreground color 
          if      (code>=90  && code<=97 ) fg = color_cycle[code-90+8];
          //100–107 Set underline color
          else if (code>=100 && code<=107) ul = color_cycle[code-100+8];
      } // end switch
    } // end parameter loop
  }
  else 
  {
    // Control cod is neither navigation nor style selector  
    // It might be one of these reset commands: 
    byte n;
    switch (cs_final_byte) {
      case 'J': // Vertical clear/reset commands
        cstamp();
        n=nread?cs_parse_buff[0]:0;
        switch (n) {
          case 0: clear_right(); clear_below(); break;
          case 1: clear_left();  clear_above(); break;
          case 2: // clear: 2:screen 3:screen+scrollback
          case 3: reset_screen(); break;
          default: cstamp(); return FAIL; 
        }  
        cstamp(); 
        break;
      case 'K': // Horizontal clear/reset commands
        cstamp(); 
        n=nread?cs_parse_buff[0]:0;
        switch (n) {
          case 0: clear_right(); break;
          case 1: clear_left();  break;
          case 2: clear_line();  break;
          default: cstamp(); return FAIL;
        }  
        cstamp(); 
        break;
      case 'S': n = nread?cs_parse_buff[0]:1; cstamp(); scroll(n);  cstamp(); break; // Scroll up
      case 'T': n = nread?cs_parse_buff[0]:1; cstamp(); scroll(-n); cstamp(); break; // Scroll down
      case 'n': // '6n' is REQUEST_POSITION
        if (!(nread && cs_parse_buff[0]==6)) return FAIL;
        Serial.write("\x1b[");
        serial_write_decimal(row);
        Serial.write(';');
        serial_write_decimal(col);
        Serial.write('R');
        break;
      case 's': save_cursor();    break; // save cursor
      case 'u': restore_cursor(); break; // restore cursor
      default: return FAIL;
    }
  }
  return SUCCESS;
}


#endif //CONTROL_H
