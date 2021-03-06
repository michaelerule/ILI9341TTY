#!/usr/bin/env python3
'''
Prepares data and some of the source code to handle combining diacritics

- Diacritic bitmaps are squished into a byte array, one byte per pixel row. 
- Diacritics are define with 2 bytes of information:
    - An info code, which packs height, padding, and location in 2,2,4 bits.
    - An index into the bitmap data for the start of this diacritic
'''
from CONFIG import *

C_SOURCE   = ''
headername = diacritics_filename.split('/')[-1].split('.')[0].upper()
C_SOURCE += "#ifndef %s_H\n"%headername
C_SOURCE += "#define %s_H\n"%headername
C_SOURCE += '// This file is automatically generated, do not edit it,\n'
C_SOURCE += '// see ./prepare_fonts/README.md for more information. \n'
C_SOURCE += '\n'
C_SOURCE += '// 0x000300-0x00036F: Combining Diacritical Marks '

# Diacritics from the "combining diacritics" unicode block are used as trasformations
# Define their names here. 
C_SOURCE += '\n'
for i in range(0x300,0x036F+1):
    C_SOURCE+='#define %s 0x%X   // %s\n'%(unicodedata.name(chr(i)).replace(' ','_').ljust(36),i-0x300,chr(i))
C_SOURCE += '\n'


location_codes = ('ABOVE_LEFT ABOVE_RIGHT BELOW_LEFT BELOW_RIGHT'
                 ' LEFT RIGHT ABOVE BELOW OVERLAY').split()
rename = {
    'OVERLINE':'HLINE',
    'LOW LINE':'HLINE BELOW'
}
all_marks      = []
bitinfo        = {}
padinfo        = {}
aliases        = {}
active         = None
alreadydefined = False
diacritic_info = ''.join(open(combining_modifiers_file,'r').readlines()).split('\n')

for line in diacritic_info:
    if line.startswith('0x'):
        # Start reading information for new diacritic
        code = line[:6]
        char = line[6]
        name = line[9:]
        assert name.split(' ')[0]=='COMBINING'
        for k,v in rename.items():
            name = name.replace(k,v)
        name = ' '.join(name.split(' ')[1:])
        
        # Try to guess the correct location from the name
        location = 'ABOVE'
        for l in location_codes:
            if name.endswith(l.replace('_',' ')):
                location = l
                name = ' '.join(name.split(' ')[:-len(l.split('_'))])
                break 
        if 'GREEK' in name:
            location = 'GREEK'
        if 'GREEK DIALYTIKA TONOS' in name:
            location = 'ABOVE'
        if 'CEDILLA' in name or 'OGONEK' in name:
            location = 'BELOW'
        if name=='HORN':
            location = 'ABOVE_RIGHT'
            
        # Set the actively-being-read diacritic information
        active = (code,char,name,location)
        #print('code:',code,'char:',char,'name:',name,'where:',location)

        # Create space to store bitmap, if needed
        alreadydefined = name in bitinfo and len(bitinfo[name])>0
        if not alreadydefined: 
            bitinfo[name] = []
        all_marks.append(active)
        padinfo[code]=1
    elif active!=None:
        #  Read bitmap, alias, or padding information for current diacritic
        if line.startswith('pad'):
            code = active[0]
            padinfo[code] = int(line.split('pad')[1])
        elif line.startswith('alias'):
            alias = line.split('alias')[1].strip().upper()
            name  = active[2]
            aliases[name] = alias
        elif len(line) and all([c in '01' for c in line]):
            if not len(line)==CW:
                print('code:',code,'char:',char,'name:',name,'where:',location)
                raise ValueError('Expected bitmap row width to equal to chararacter width %d'%CW)
            if alreadydefined:
                raise ValueError('A bitmap is already defined for '+active[2])
            
            bitinfo[active[2]].append(line)
        elif not len(line.strip())==0:
            raise ValueError('Unexpected line format: '+line)

def packbits(b):
    return (2**arange(CW))@array([bi=='1' for bi in b])

# Bitinfo stores diacritic bitmaps
# Keys are the "name" for each diacritic
# We need to tell the code where to find each bitmap
# To do that, we pack the bitmaps into an array and
# record where each one starts (an how many bytes long it is)
offset  = 0
offsets = {}
alldata = []
lengths = {}
for k,v in bitinfo.items():
    offsets[k] = offset
    lengths[k] = len(v)
    offset += len(v)
    alldata+=[packbits(b) for b in v][::-1]

nq = len('BELOW_RIGHT')
location_codes = {'ABOVE':0,
    'BELOW':1,
    'OVERLAY':2,
    'LEFT':3,
    'RIGHT':4,
    'ABOVE_LEFT':5,
    'ABOVE_RIGHT':6,
    'BELOW_LEFT':7,
    'BELOW_RIGHT':8,
    'GREEK':9}

defined_codes = set()
codedata = {}
for code, ch, descr, location in all_marks:
    lookup = descr

    # Check if this diacritic is aliased to another diacritic
    if lookup in aliases:
        lookup = aliases[lookup]

    # Calculate offset into "combining diacritics" block
    i = int(code[2:],16)-0x300

    # Check if this diacritic has been defined
    if not lookup in bitinfo or len(bitinfo[lookup])<=0:
        # Insert dummy info into the table if not defined
        # (double-width diacritics are not defined)
        codedata[i] = (0xff,0,0,0)
        continue

    # Bitmap location and length taken from "lookup" (may be aliased)
    # Padding/spacing information taken from "code" (not aliased)
    codedata[i] = (offsets[lookup],
        lengths[lookup],
        padinfo[code]+1,
        location_codes[location])
    defined_codes.add(i)

a = np.min([*defined_codes])
b = np.max([*defined_codes])+1
C_SOURCE+=('// defined codes range from 0x300+ %d..%d'%(a,b))+'\n'
l = b-a
bytedata = zeros(l*2,'u8')

for i in range(a,b):
    l,n1,n2,n3 = codedata[i]
    byte1 = l&0xff
    byte2 = (((n1-1)&0b11)<<6) | (((n2)&0b11)<<4) | (n3&0b1111)
    j = i-a
    bytedata[j*2:j*2+2] = [byte1,byte2]

for k,v in location_codes.items():
    C_SOURCE+=('#define %s (%d)'%(k.ljust(nq),v))+'\n'
C_SOURCE+=('#define UNDEFINED (0xFF)')+'\n'
C_SOURCE+=('#define MAX_DIACRITIC_CODE (%d)'%(b-1))+'\n'
def pack80(name,data):
    global C_SOURCE
    line = 'static const uint8_t %s[%d] PROGMEM = {'%(name,len(data))
    for i in data:
        s = '%d,'%i
        if len(line)+len(s)>80:
            C_SOURCE+=(line)+'\n'
            line = '  '
        line += s
    C_SOURCE+=(line+'};')
    

C_SOURCE+=('''\n
// Diacritic bitmaps are organized into rows, with leftmost pixel in the lowest
// -order bit. Bitmaps of varying height are packed consecutively. To retrieve
// a bitmap, unpack the information in the `diacritic_info' array.''')+'\n'
pack80('diacritic_bitmaps',alldata)
C_SOURCE+=('''\n
// The `diacritic_info` array decribes diacritics, starting at 0x300, in two-
// byte codes. The first byte is the starting index for the bitmap information
// in `diacritic_bitmaps`, or 0xFF is the diacritic is not supported. The
// second byte contains the height (minus 1), padding (1=no padding), and
// location (see #defined location codes above), packed into 2, 2, and 4 bits,
// respectively.''')+'\n'
pack80('diacritic_info',bytedata)
# Check we're not wasting space
assert (len(alldata) + len(bytedata)) < ((b-a)*4)

C_SOURCE+=('\n\n')
C_SOURCE+='''

////////////////////////////////////////////////////////////////////////////////
/** Stamp combining diacritic over previously drawn character
 */
void stamp_diacritic(byte index,byte nrow,byte pad,byte location) {
  byte rowdata[nrow];
  for (int i=0; i<nrow; i++) rowdata[i] = pgm_read_byte(diacritic_bitmaps+index+i);
  if (location==GREEK) {
    // Greek breathing marks are above for lower-case and above-left for upper case
    // Handle this by routing to ABOVE or ABOVE_LEFT depending on character height
    // Start at topmost row
    int i=CH-1;
    // Move down until we find a non-empty row
    while (char_bitmap[i]==0 && i>0) i--;
    location = i>MIDLINE? ABOVE_LEFT : ABOVE;
  }
  if (location==ABOVE_RIGHT || location==BELOW_RIGHT) {
    // Move the mark as far right as possible. 
    // Find rightmost column of diacritic bitmap
    byte mask = 0;
    int i=0;
    for (; i<nrow; i++) mask |= rowdata[i];
    mask <<= (8-CW);
    byte counter = 0;
    // Shift left until we get a 1 in the top bit
    while ((int8_t)(mask)>0) {mask<<=1; counter++;}
    // "Counter" now tells us how many bits we need to shift to meet right column
    for (i=0; i<nrow; i++) rowdata[i]<<=counter;
    // Reduce to the ABOVE/BELOW case
    location = (location==ABOVE_RIGHT)? ABOVE: BELOW;
  }
  else if (location==ABOVE_LEFT || location==BELOW_LEFT ) {
    // Move mark as far left as possible
    byte mask = 0;
    int i=0;
    for (; i<nrow; i++) mask |= rowdata[i];
    byte counter = 0;
    // Shift right until we get a 1 in the top bit
    while (mask) {mask>>=1; counter++;}
    // "Counter" now tells us how many bits we need to shift to meet right column
    for (i=0; i<nrow; i++) rowdata[i]>>=counter;
    location = (location==ABOVE_RIGHT)? ABOVE: BELOW;
  }
  if (location==ABOVE) {
    // Find top of character
    int i=CH-1;
    while (i>=MIDLINE && !char_bitmap[i]) i--;
    // Handle i,j as special cases
    if (char_bitmap[i]==0b00001000 && char_bitmap[i-1]==0) {
      // diacritics overwrite the tittle on these
      char_bitmap[i] = 0;
      while (i>=MIDLINE && !char_bitmap[i]) i--;
    }
    // i will stop at first non-empty row
    // ideally, diacritic should be placed above this
    // pad matters
    // pad 0 = overlap top
    // pad 1 = abut top
    // pad 2 = leave spacing
    byte diacritic_start_row = i+pad;
    int last_row = (nrow-1)+diacritic_start_row;
    if (last_row>=CH) {
      // Not enough space
      int need_space = last_row - (CH-1);
      while (need_space>0 && SUCCESS==shorten_down_top()                      ) {need_space--; diacritic_start_row--;}
      while (need_space>0 && SUCCESS==nudge_down_top()                        ) {need_space--; diacritic_start_row--;}
      while (need_space>0 && SUCCESS==smash_diacritics_down_top_conservative()) {need_space--; diacritic_start_row--;}
      while (need_space>0 && SUCCESS==smash_diacritics_down_top_aggressive()  ) {need_space--; diacritic_start_row--;}
      while (need_space>0 && pad>0) {pad--; need_space--; diacritic_start_row--;}
    } else if (i==MIDLINE-1) {
      byte isempty = 1;
      do {
        if (char_bitmap[i]) {
          isempty = 0;
          break;
        }
        i--;
      } while (i>=0);
      if (isempty) diacritic_start_row = CH - 1 - nrow;
    
    }
    // We might run out of space, for now just stop drawing if this happens
    for (int i=0; i<nrow; i++) {
      if (i+diacritic_start_row >= CH) break;
      char_bitmap[i+diacritic_start_row] |= rowdata[i];
    }
  }
  else if (location==BELOW) {
    // Find base of character
    int i=0;
    while (i<CH && char_bitmap[i]) i++;
    if (i < nrow + pad - 1) {
      int need_space = nrow + pad - 1 - i - 2;
      while (need_space>0 && SUCCESS==shorten_up_base()                      ) need_space--;
      while (need_space>0 && SUCCESS==nudge_up_base()                        ) need_space--;
      while (need_space>0 && SUCCESS==smash_diacritics_up_base_conservative()) need_space--;
      while (need_space>0 && SUCCESS==smash_diacritics_up_base_aggressive()  ) need_space--;
      while (need_space>0 && pad>0) {pad--; need_space--;}
    }
    byte r = 0;
    for (int i=0; i<nrow; i++) {if (r+i>=CH) break; char_bitmap[r+i] |= rowdata[i];}
  }
  else if (location==OVERLAY) for (int i=0; i<nrow; i++) char_bitmap[MIDLINE+i-nrow/2] |= rowdata[i];
}

////////////////////////////////////////////////////////////////////////////////
// Combine mark from the combining diacritics unicode block

void combine_diacritic(byte diacritic_index) {
  if (diacritic_index>MAX_DIACRITIC_CODE) return;
  byte index = pgm_read_byte(diacritic_info + diacritic_index*2);
  if (index==UNDEFINED) return;
  byte info = pgm_read_byte(diacritic_info + diacritic_index*2 + 1);
  byte loc  = info & 0b1111;
  byte pad  = (info>>4) & 0b11;
  byte nrow = ((info>>6) & 0b11) + 1;
  stamp_diacritic(index,nrow,pad,loc);
}

////////////////////////////////////////////////////////////////////////////////
/** Handling combining diacritic. 
 *  There must be a recently-drawn charater with which to combine. 
 *  If there isn't, treat it as combining with an empty space. 
 */
int _combiningdiacriticalmarks(unsigned int c) {
  if (combining_ok!=0) {
    // If there is some character with which to combine...
    row = prev_row; col = prev_col; 
    combine_diacritic(c);
  } else {
    // Nothing to combine with... treat as combining with space
    for (byte i=0; i<CH; i++) char_bitmap[i]=0;
    combine_diacritic(c);
  }
  new_combining_ok = 1;
  return LOADED;
}
'''


# Write header file
C_SOURCE+=('\n\n#endif // %s\n'%headername)
with open(diacritics_filename,'wb') as f:
    f.write(C_SOURCE.encode('utf8'))
    f.flush()
    f.close()

