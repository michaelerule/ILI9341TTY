#!/usr/bin/env python3


"""
Prepare the header file which defines the main font data

TODO

- Characters are defined if they are used in the mapping
- Transformations are defined only if they are used in the mapping
- A warning is given for glyphs that are never used
- A warning is given for transforms that are never used

Issue: for compactness we require that sparsely-packed blocks cover a range
of no more than 256 codepoints. This allows us to store a list of which code-
points are included in single bytes. However, some sparse blocks are larger
than this. 

Issue: there is a lot of code duplication in assigning each block its own
function. There are only three options: sparse block, dense block, or
soft-mapped. Only the soft-mapped fonts need their own dedicated functions. 

So maybe the unicode mapping routine could encounter the following instead:
- A 2-bit flag indicating the type of block (dense, sparse, softmapped, NULL)
- A 6-bit index telling us where to find information to go next. 

For dense blocks we need 
- Starting index
- Stopping index
- Pointer to start of list of uint16_t-packed glyph+transform codes

For sparse blocks we need
- Starting index
- Stopping index
- Pointer to start of list of uint16_t-packed glyph+transform codes
- Number of codepoints mapped
- Pointer to sorted list of mapped offsets

For soft-mapped blocks we need
- Function pointer to rendering code

Large sparse blocks already need to be split into <=256 length portions. 
Does it make sense to further sub-divide blocks? Some blocks might be 
better represented as a mixture of dense ranges and sparse ones? This might
save space, but it too complicated for me to think about right now!

But yes, large sparse blocks need to be broken up. 
Also glyphs that aren't mapped should be discarded. 
Ok this is too much for me to fit into my head at the moment. 
Shortest path back to something that might compile? 
We do need to save space!
Covert unicode range search to re-use range search from here.
Get it compiling to see how much space we're missing
We'll need to delete the current glyph map. 
finally, we'll need to change all these glyph constants to reflect the new
ordering. We'll need to put the replacement character back. And handle space. 
Ok we got the replacement character and space back. So what next? 
We need to repair the code point mapping. 
Let's split this into two separate channels. 
Ok, what to do with too many characters? 
We need to define extra transformation codes.
Pre-combine these with the base glyph code.
So we need to know how many extra codes are needed. 
So we need to define some extra transformation codes to handle this. 


Further notes: 

We might want to re-order glyphs. The transform table may only need to access 
certain glyphs in combination with transfomations. The remainder of the glyphs 
might be "one offs", and used at most as aliases for multiple characters. 

For this, it would suffice to define a new transformation code for "one off", 
which tells the code to search for the glyph in a different table. This might 
allow a broader support of different alphabets.

This would require the unicode mapping code to interact with the glpyh
packing code. 

First steps toward this: 

- Figure out which glyphs are used only as on-offs, never with a transform
- Propose a canonical re-packing of the glpyhs (keep ASCII in the same place)

We've ensured that all ASCII glyphs are 5x10. Some of the other ones are
5x11 but these are rare. (Integral signs in mathematicaloperators). 
Other blocks need 5x12 (Bracket/integral pieces in miscellaneoustechnical).
Ideally these should be packed and treated differently, to save space. 
It would be nice to automate this but, reasonably this might not be possible.
We can try this: 

- Parse glyph files
- Compute tight bounding box for ascii
- Figure out which glyphs fit into this size
- Pack everything else in a separate texture

This is going to get messy. Best to abstract it: auto-generate some code that
just does "get me the bits for the glyph at this index, I don't care how you
do it".

Densly-packing each character might not be smart. It might be smarter
to structure all the glyph bitmaps as a single row, and dense-pack each
pixel-row of this. That way, one can just read off K<CH bytes, apply the
same shift+mask operation to each byte, and done!

Permuting the glyphs so we pack them in the minimum-size arrays might make
sense. This breaks the fast-path for ASCII, though. It would cost 65 bytes
to store a permutation for ASCII to compensate. 

# _geometricshapes is an ugly special case
if codename=='geometricshapes':
    SOURCE+=('''// Special case: Some parts of geometric shapes stored elsewhere
    // This whole block is going to need to switch to softmapped
      switch (c) {
        // Semigraphic-like geometric shapes (design to combine)
        case 54: return _symbolsforlegacycomputing(207); // ◖
        case 55: return _symbolsforlegacycomputing(208); // ◗
      }
      // Some stray symbols in the geometric symbols block that should 
      // be interpreted like teletext characters
      if (c>=66 && c<=69) {
        uint8_t color1 = invert? bg : fg;
        uint8_t color2 = invert? fg : bg;
        switch (c) {
          // 1/3 in 1 is slope 1 so 3/3 in one is slope 3
          case 66:  draw_ttxt( 3, 0, color1, color2); break; // ◢
          case 67:  draw_ttxt(-3, 3, color1, color2); break; // ◣
          case 68:  draw_ttxt( 3, 0, color2, color1); break; // ◤
          case 69:  draw_ttxt(-3, 3, color2, color1); break; // ◥
        }
        advance_cursor(1);
        return SUCCESS;
      }
    ''')
"""


# These base glyphs are required by some of the unicode blocks handled in
# software. 

enclosed_alphanumerics_base_glyphs = (
  'O123456789⒑⒒⒓⒔⒕⒖⒗⒘⒙⒚⒛'
  'abcdefghijklmnopqrstuvwxyz'
  'ABCDEFGHIJKLMNOPQRSTUVWXYZ')

mathematical_alphanumerics_base_glyphs =(
  'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  'abcdefghijklmnopqrstuvwxyzıȷ'
  'ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡϴΣΤΥΦΧΨΩ∇'
  'αβγδεζηθικλμνξοπρςστυφχψω∂ϵϑϰϕϱϖϜϝ'
  '0123456789')


import unicodedata
import re
from pylab          import *
from CONFIG         import *
from font_utilities import *
from collections    import defaultdict

################################################################################
# Start of header for unicode mapping file
SOURCE   = ''
headername     = unicode_mapping_filename.split('/')[-1].split('.')[0].upper()
codeheadername = glyphcodes_filename.split('/')[-1].split('.')[0].upper()
SOURCE     += "#ifndef %s_H\n"%headername
SOURCE     += "#define %s_H\n"%headername
SOURCE     += '''
// This file is automatically generated, do not edit it,
// see ./prepare_fonts/README.md for more information.
#define  REPLACEMENT_CHARACTER (0)
#define  FIN {advance_cursor(1); return SUCCESS;}
#include "terminal_misc.h"
#include "TFT_macros.h"
#include "glyphcodes.h"
#include "combining_diacritics.h"
#include "softfonts.h"
#include "textgraphics.h"
int  handle_transform(unsigned int transform_code);
byte load_glyph_bitmap(unsigned int base_glyph);
'''
# Moving the #defines for glyph and transform codes into a separate file
CODESOURCE  = ''
CODESOURCE += "#ifndef %s_H\n"%codeheadername
CODESOURCE += "#define %s_H\n"%codeheadername
CODESOURCE += '// This file is automatically generated, do not edit it,\n'
CODESOURCE += '// see ./prepare_fonts/README.md for more information. \n\n'
CODESOURCE += '// mapping tables use this many bits to store character index\n'
CODESOURCE += '#define TRANSFORMBITS (%d)\n\n'%TRANSFORMBITS
CODESOURCE += '// mapping tables use this many bits to store transform index\n'
CODESOURCE += '#define CHARBITS (%d)\n\n'%CHARBITS
CODESOURCE += '// maximum number of base glyphs supported\n'
CODESOURCE += '#define MAXNCHAR (1<<CHARBITS)\n\n'
CODESOURCE += '// maximum number of transformation codes that can be supported\n'
CODESOURCE += '#define MAXNMODS (1<<TRANSFORMBITS)\n'

################################################################################
# Load glyph mapping: which base characters are available as glyphs?
with open(main_glyph_unicode_points,'r') as f:
  lines = []
  for il,l in enumerate(f.readlines()):
    l = l.replace('\n','')
    if len(l): 
      if len(l)>NGLYPHCOLS:
        raise ValueError(
        'Parsing %s, line %d: expected <=%d chars in this line:'\
         %(main_glyph_unicode_points,il,NGLYPHCOLS)
         +'\n'+l)
      lines.append(l)
  codepoints = tuple(lines)
# ______________________________________________________________________________
# Check that codepoints are formatted as we expect
for i,l in enumerate(codepoints[:-1]):
  if not len(l)==32:
    raise ValueError('Expected 32 chars on line %d, found %d: %s'%(i+1,len(l),l))
assert len(codepoints[-1])<=32
codepoints = ''.join(codepoints)
# ______________________________________________________________________________
# Load glyph alias information
# The list of codepoints in each line of this file will be treated as 
# graphically identical in our font
aliases = []
with open(glyph_aliases_filename,'r') as f:
  for line in f.readlines():
    line = line.replace('\n','')
    aliases.append(sorted(list(set(line))))
aliasmap = rebuild_aliasmap(aliases, codepoints)
# ______________________________________________________________________________
# Convert all code points for the base glyphs to their lowest alias
canoncode = ''
for ic,c in enumerate(codepoints):
  if c==' ': 
    canoncode+=' '
    continue
  a = aliasmap.get(c,c)[0]
  if a in canoncode:
    print('Row %d Column %d; %s'%(ic//32,ic%32,c))
    raise ValueError('character %s with alias %s (%x) is aleady mapped'\
      %(c,a,ord(a)))
  canoncode+=a
# ______________________________________________________________________________
# Generate abbreviations for glyphs
# This lets us refer to them in the source code in a semi-human-readbale way.
abbreviation_map = {}
codepoint_names  = {}
for c in canoncode:
  c = aliasmap.get(c,c)[0]
  shortname, name = generate_codepoint_name_abbreviation(c, aliases, abbreviation_map)
  codepoint_names[c]=(shortname, name)
abbreviation_map['◌'] = '_COMB_'

inverse_abbreviation_map = {v:k for k,v in abbreviation_map.items()}
# ______________________________________________________________________________
# Get transformation commands, their names, and abbreviations
# Most of these are combining modifiers, so we just need to define the 
# Glyph Ε and then can define Ë É È Ě etc as transforms of this base
# glyph. But we also define some odd ones like reflections, adding strokes, 
# etc, which aren't in the combining diacritics block. 
# Ensure there are no duplicate abbreviations for the transforms, and add the 
# "long name" to the python namespace so that character decompositions can refer
# to it
execfile(transform_commands_filename, globals())
command_dictionary = {}
for i,(shortname,(longname,csourcecode)) in enumerate(commands):
    if shortname in command_dictionary:
        raise ValueError(('Command %d (%s): '
            'The abbreviation %s is already used for %s')\
        %(i,longname,shortname,command_dictionary[shortname]))
    command_dictionary[shortname] = (longname,csourcecode)
    globals()[longname]=shortname
commands = command_dictionary
# ______________________________________________________________________________
# Load character decomposition information
# This represents unicode characters as a base glyph + transformation
# Ensure decomposed characters represented in terms of canonical alias
execfile(character_decompositions_filename, globals())
newdecompose = {}
for k,v in decompose.items():
    k = aliasmap.get(k,k)[0]
    if len(v)<2: continue
    base = aliasmap.get(v[0],v[0])[0]
    transform_command = v[1:].upper()
    if not transform_command in commands: continue
    newdecompose[k] = base+transform_command
decompose = newdecompose

# ______________________________________________________________________________
# Load information on unicode blocks (pulled from Wikipedia), removing blocks
# that aren't implemented via unicode-point mapping (soft-mapped)
# Then determine which characters are potentially mapped.
# Iterate over all mapped unicode blocks
# Iterate over all characters within each block
# Look up its name using the `unicodedata` library
# Add its name to the set of potentially mapped characters
# (only characters that are defined in terms of a base glyph, an alias, or
# a transformation will actually get mapped)
blockinfo = get_unicode_blocks_information()
blockinfo = {k:v for (k,v) in blockinfo.items() if k in mapped_blocks}
mapped = set()
for shortname,(name,start,stop,nassigned) in blockinfo.items():
  if stop-start>=256:
    print (shortname,name,start,stop,nassigned)
    raise ValueError('For now, blocks must have <=256 characters. '+\
      'Block %s has %d'\
      %(shortname,stop-start))
  for i in range(start,stop+1):
    c = chr(i)
    try:
      name = unicodedata.name(c)
      mapped.add(c)
    except ValueError:
      continue
# ______________________________________________________________________________
# Check all characters and how each one is defined
# Check which base characters and transforms are actually used
# This iterates over all characters to be mapped. 
# First we check if the character is a base glyph or is aliased to a base glyph.
# If not, we check if it is defined as a decomposed (transformed, modified, 
# combined) character. If it is, and if the required base glyph exists, then
# we add it's base glyph and transform to the list of required glyphs and 
# transforms. 
# If this fails, mark the character as undefined. 
# ______________________________________________________________________________
# Also convert aliases for base glyphs used by enclosed/mathematical alphanumerics
enclosed_alphanumerics_base_glyphs     = ''.join([aliasmap.get(c,c)[0]
  for c in enclosed_alphanumerics_base_glyphs])

mathematical_alphanumerics_base_glyphs = ''.join([aliasmap.get(c,c)[0]
  for c in mathematical_alphanumerics_base_glyphs])

required = set(enclosed_alphanumerics_base_glyphs) | \
           set(mathematical_alphanumerics_base_glyphs)

print(required)

base_glyphs_used    = set(required)
transforms_required = set()
missing_bases       = set()
undefined_chars     = []
for ch0 in mapped: 
    # Convert to canonical alias if one exists
    ch = aliasmap.get(ch0,ch0)[0]
    # Is it supported as a base glyph?
    if ch in canoncode: base_glyphs_used.add(ch)
    # Is it supported as a transformed glyph
    elif ch in decompose:
        d = decompose[ch]
        base_glyph = aliasmap.get(d[0],d[0])[0]
        transform  = d[1:]
        if base_glyph == '◌':
          # Special situation: there is no base character, the transform is 
          # applied to and replaces the previously-drawn glyph, if any. To do 
          # this, we use a base character code of 1. For now we abuse the ◌ 
          # character to signal this. 
          transforms_required.add(transform)
        else:
          # Transform will only be used if the required base glyph exists
          if base_glyph in canoncode:
              base_glyphs_used.add(base_glyph)
              transforms_required.add(transform)
          else:
              undefined_chars.append(ch0)
              missing_bases.add(ch0)
    else:
        undefined_chars.append(ch0)
# ______________________________________________________________________________
# Print out some reporting information
print('')
print('PREPARE_UNICODE_MAPPING: These points are mapped but not defined:')
print(' '.join(sorted(list(undefined_chars))))
print('')
print('PREPARE_UNICODE_MAPPING: These glyphs are defined but never used:')
unused_glyphs = set(canoncode) - base_glyphs_used
print(' '.join(sorted(list(unused_glyphs),key=lambda i:ord(i))))
print('')
print('PREPARE_UNICODE_MAPPING: These transforms are required but never defined:')
missing_transforms = transforms_required-set(commands.keys())
print(' '.join(sorted(list(missing_transforms))))
print('')
print('PREPARE_UNICODE_MAPPING: These transforms are defined but never used:')
unused_transforms = set(commands.keys()) - transforms_required
print(' '.join(sorted(list(unused_transforms))))
print('')
print('PREPARE_UNICODE_MAPPING: Base glyphs were missing for these composed characters:')
print(' '.join(sorted(list(missing_bases))))
print('')   
# ______________________________________________________________________________
# remove unused commands from commands.items()
for t in unused_transforms:
    del commands[t]
# ______________________________________________________________________________
# Define commands to indicate extended code pages
nglyphs     = len(canoncode)
excess      = nglyphs - MAXNCHAR + 2
extra_pages = int(ceil(excess/MAXNCHAR))
print('There are %d glyphs;'%len(canoncode),
  'With %d bits,'%CHARBITS,
  'no more than %d glyphs can be used with transforms;'%(MAXNCHAR-2),
  'There are %d extra glyphs;'%excess,
  'I can store the extra in %d extra code pages;'%extra_pages,
  '(These will need to be implemented as extra "transform" commands',
  'to select a codepage)')

for i in range(extra_pages):
  p = i+2
  commands['EP%d'%p] = ('EXTENDED_CODEPAGE_%d'%p,'')

# ______________________________________________________________________________
# Verify that all used base glyphs exist
# And that all base glyphs are defined
if not len(base_glyphs_used)==len(base_glyphs_used&set(canoncode)):
  missing = base_glyphs_used - set(canoncode)
  raise ValueError('The following required base-glyphs are missing: '+
    ''.join(sorted(list(missing))))

assert len(base_glyphs_used - set(canoncode))==0
assert all([c in canoncode for c in enclosed_alphanumerics_base_glyphs])
assert all([c in canoncode for c in mathematical_alphanumerics_base_glyphs])

# ______________________________________________________________________________
# TODO: Figure out which transforms are actually just calling out to 
# TODO: We want to do something clever with mapping codes directly. 
# Group them at the end in a single range? 
# Use a table to look them up? 
# the combining diacritics code.
# TODO: 
# Figure out which transforms can be supported by a call out to the diacritics
# Bulid an index to map these without using the switch block
# Diacritics from the "combining diacritics" unicode block are used as trasformations
# Define their names here. 
diacritics_name_map   = {}
diacritics_number_map = {}
for i in range(0x300,0x036F+1):
    diacritic_name   = unicodedata.name(chr(i)).replace(' ','_')
    diacritic_number = i-0x300
    diacritics_name_map  [diacritic_name  ] = diacritic_number
    diacritics_number_map[diacritic_number] = diacritic_name

# glob form: combine_diacritic(*); in regex form:
print('The following transforms are handled as combining diacritics:')
pattern = re.compile(r'combine_diacritic\((?:(?!\);)(?:.|\n))*\);')
diacritic_transforms = {}
for shortname,(longname,sourcecode) in commands.items():
    match = pattern.fullmatch(sourcecode)
    if match:
        argument = sourcecode.split('combine_diacritic(')[-1][:-2]
        print('  ',shortname,longname,'→',argument)
        diacritic_transforms[shortname]=(longname,sourcecode,argument)

################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
# Start of source code
# ______________________________________________________________________________
# Some transforms (reflections) call out to subroutines
# Define any new subroutines in <transform_subroutines_filename>.
# They are added to the source code here. 
SOURCE+='\n'+'/'*80
SOURCE+="""
// Helper routines for transformations

// Mirror horizontally for even-width charactes
// Set nudge to 1 to reflect rightmost 5 pixels
void mirror_horizontal(byte nudge) {
  for (byte i=0; i<CH; i++) {
    // Specialized for 6-px wide fonts
    byte b = char_bitmap[i] & 0b111111;
    b >>= nudge;
    // 123456 -> 456123
    b = ((0b000111&b)<<3)|((0b111000&b)>>3);
    // 456123 -> 654321
    b = ((0b100100&b)>>2)|((0b001001&b)<<2)|(0b010010&b);
    char_bitmap[i] = b;
  }
}

// Flip rows in character bitmap
#define FLIP_CBM(a,b) {byte temp=char_bitmap[a]; char_bitmap[a]=char_bitmap[b]; char_bitmap[b]=temp;}
void mirror_vertical_helper(byte rstart, byte rstop) {
  byte i;
  for (i=rstart; i<=rstop; i++) FLIP_CBM(rstop-i,i);
  while (i<CH) char_bitmap[i++]=0;
}
// Flip vertically; Specialized for 12x6 fonts
// 01 2345678 9AB --> BA 9876543 210
#define mirror_vertical()           {mirror_vertical_helper(6,11);}
// Flip vertically for upper-case letters; Specialized for 12x6 fonts
// 01 2345678 9AB --> A9 8765432 10X
#define mirror_vertical_uppercase() {mirror_vertical_helper(6,10);}
// Flip lower-case letter vertically; Specialized for 12x6 fonts
// 01 23456 789AB --> 87 65432 10xxx
#define mirror_vertical_lowercase() {mirror_vertical_helper(5, 8);}

////////////////////////////////////////////////////////////////////////////////
// Binary search for codepoint index for sparsely-packed blocks
uint8_t binary_search(
  const byte i, 
  const byte nlist, 
  const byte *sorted_list) 
  {
  uint8_t lo = 0;
  uint8_t hi = nlist;
  //Serial.print("Low: "); //Serial.println(lo);
  //Serial.print("High: "); //Serial.println(hi);
  while (hi>lo) {
    uint8_t midpoint = (lo+hi)/2;
    unsigned int a = pgm_read_byte(&sorted_list[midpoint]);
    //Serial.print("Low: "); //Serial.println(lo);
    //Serial.print("High: "); //Serial.println(hi);
    //Serial.print("midpoint:  "); //Serial.println(midpoint);
    //Serial.print("a: "); //Serial.println(a);
    if      (i>a) lo=midpoint+1;
    else if (i<a) {
      if (midpoint) hi=midpoint-1;
      else return -1;
    }
    else return midpoint;
  }
  // Ran off beginning of list
  if (hi<lo) return (-1);
  // Handle high==low case: test and return if in range
  unsigned int a = pgm_read_byte(&sorted_list[lo]);
  if (i==a) return lo;
  return (-1);
}

////////////////////////////////////////////////////////////////////////////////
// Binary search for glyph group based on glyph index
int8_t binary_search_range(
  const unsigned int  i, 
  const byte          nlist, 
  const unsigned int *start_idxs, 
  const byte         *lengths)
  {
  int8_t lo = 0;
  int8_t hi = nlist;
  while (hi>lo) {
    int8_t midpoint = (lo+hi)/2;
    unsigned int a = pgm_read_word(&start_idxs[midpoint]);
    unsigned int b = pgm_read_byte(&lengths   [midpoint]) + a;
    if (i>=a) {
      if (i<b) return midpoint;
      lo=midpoint+1;
    }
    else hi=midpoint-1;
  }
  // Ran off beginning of list
  if (hi<lo) return (-1);
  // Handle high==low case: test and return if in range
  unsigned int a = pgm_read_word(&start_idxs[lo]);
  unsigned int b = pgm_read_byte(&lengths   [lo]) + a;
  if (i>=a && i<b) return lo;
  return (-1);
}
"""


# ______________________________________________________________________________
# Define abbreviated names of each transformation. These are used in the 
# generated mapping tables in the C source code. 
CODESOURCE+='\n\n'+('/'*80+'\n// Transformation command codes:\n')
i = 1
# Start with the easy ones: those that call out to combining diacritics
ordered_abbreviations = []
ordered = list(diacritic_transforms)
for abbreviation in ordered:
    longname,sourcecode,argument=\
        diacritic_transforms[abbreviation]
    c_define = '%s%s'%(transform_code_prefix, abbreviation.ljust(3))
    CODESOURCE+=('#define %s (%3d) // %s (combining modifier)'%(c_define.ljust(8),
                                         i*MAXNCHAR, longname))+'\n'
    ordered_abbreviations.append(abbreviation)
    i+=1
#Now everything else, which will go into a giant switch statement
for abbreviation, description in commands.items():
    if abbreviation in diacritic_transforms:
        continue
    if isinstance(description,tuple):
        # Transform code exists
        description = description[0]
    else:
      raise ValueError('Source code not defined for %s %s'%(abbreviations, description))
    c_define = '%s%s'%(transform_code_prefix, abbreviation.ljust(3))
    CODESOURCE+=('#define %s (%3d) // %s'%(c_define.ljust(8), i*MAXNCHAR, description))+'\n'
    ordered_abbreviations.append(abbreviation)
    i+=1
# Ensure we have enough bits to encode all transform codes!
assert i<MAXNMODS
NUMBER_OF_TRANSFORMS = i


################################################################################
################################################################################
################################################################################
################################################################################  
# ______________________________________________________________________________
# Pack a lookup table of "transforms" that are really just combining modifiers
# 
N_TRANSFORM_COMBINING = len(diacritic_transforms)
SOURCE += '''#define N_TRANSFORM_COMBINING (%d)
static const byte modifier_transforms[N_TRANSFORM_COMBINING] PROGMEM = {
'''%N_TRANSFORM_COMBINING

for abbreviation in ordered:
  longname,sourcecode,argument=diacritic_transforms[abbreviation]
  SOURCE+='  %s,\n'%argument
SOURCE+='};\n\n'



# ______________________________________________________________________________
# Start of the function to handle transformation code
SOURCE+=('\n'+'/'*80+'\n'+"""\
/** Many characters can be formed by transforming others.
 *  This routine accepts a "command" byte and an "index" byte. 
 *  The "index" specifies a base glyph, and the "command" specifies some way to
 *  transform this glyph.
 *  @param index: index into the character bitmap
 *  @param command: command code to transform it
 */
int handle_transform(unsigned int transform_code) {
  unsigned int base_glyph = transform_code & %s;
  unsigned int command    = transform_code & %s;

  //Serial.print("base glyph: ");
  //Serial.println(base_glyph);
  //Serial.print("command: ");
  //Serial.println(command);
  
  // Load base glyph into memory
  // TODO: we want to create some special cases
  // base_glyph = 0 --> nothing
  // base_glyph = 1 --> combining diacritic alias
  // command = any extended code page --> increment glyph index
""")%(CHARMASK,COMMANDMASK)
## Add code to handle commands here. Bare minimum for now, optimize later
if extra_pages>0:
  SOURCE += '  switch (command) {\n'
  for i in range(extra_pages):
    p = i+2
    SOURCE += '    case T_EP%d: base_glyph += %s; command=0; break;\n'%\
      (p,MAXNCHAR+i*MAXNCHAR)
  SOURCE += '  }\n'

SOURCE += """
  if (base_glyph==0) return NOT_IMPLEMENTED;
  else if (base_glyph==1) {
    // Special case: interpret transform like a combining modifier
    // and apply to previously drawn character, if possible. 
    if (combining_ok) {row=prev_row; col=prev_col;}
    else clear_bitmap();
  }
  else load_glyph_bitmap(base_glyph-1);
  
  if (command) {
    // "transforms" that just call out to combining diacritics
    byte shortened = (command >> %d) - 1;
    if (shortened<N_TRANSFORM_COMBINING)
      combine_diacritic(pgm_read_byte(modifier_transforms+shortened));
    // Else apply transformation command
    else switch (command) {
"""%(CHARBITS)
# ______________________________________________________________________________
# Store codes in ascending order in hope that compiler converts switch to a 
# jump table. Each transformation becomes an entry in a switch statement
for abbreviation in ordered_abbreviations[N_TRANSFORM_COMBINING:]:
    description = commands[abbreviation]
    if isinstance(description,tuple):
        # Transform code exists
        description, source = description
        SOURCE+='      case %s%s: { // %s\n'%(transform_code_prefix,abbreviation,description)
        source =['        '+l for l in source.split('\n')]
        SOURCE+='\n'.join(source)+'\n'
        SOURCE+='      } break;\n'
    else:
        # Not implemented yet
        SOURCE+='      case %s%s: // %s\n'%(transform_code_prefix,abbreviation,description)
        SOURCE+='        return NOT_IMPLEMENTED;\n'
        raise ValueError('!!ERROR (prepare_unicode_mapping): Transformation '
            'code %s (%s) is not defined (add this to %s to use it)'%\
            (description,abbreviation,transform_commands_filename))
# End of transformation function
SOURCE+=('''\
      default: return NOT_IMPLEMENTED;
    }
  }
  return LOADED;
}\n''')


################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
# Print packed data for each block. As we do this, keep track of empty spaces
# in dense blocks and other statistis. We'll need to collect all the sparse
# blocks toward the beginning, so we'll need to defer adding things to 
# the source code until blocks are processed and we know which ones should be
# sparse vs dense. 
blocks        = []
mapped_glyphs = set()
dense_voids   = {}
glyphs_isused = set(required)
missingblocks = []
isdense       = []
issparse      = []
for codename,(name,start,stop,nassigned) in blockinfo.items():
    blocksource = '/'*80+'\n// Data for 0x%08X-0x%08X "%s".\n'%(start,stop,name.strip())
    # Get the names for the base glyphs for all codepoints in this block
    base_names = []
    transforms = []
    for i in range(start,stop+1):
      # Get character and map to canonical alias, if any
      c = chr(i)
      c = aliasmap.get(c,c)[0]
      base_name = abbreviation_map.get(c,None)
      # Check if this is a transformed character
      transform = '0'
      if c in decompose and len(decompose[c])>1:
        q       = decompose[c][0]
        command = decompose[c][1:]
        if command in commands:
          transform = 'T_'+command
          # Check that this character isn't already defined
          if not base_name is None:
            raise ValueError(
            ('%s exists both as a base-glyph and transformed glyph.\n'%c)+
            ('The offending transform is %s:%s\n'%(c,decompose[c]))+
            ('Check %s, is %s aliased to a glyph that should be distinct?\n'\
             %(glyph_aliases_filename,c)))
          # Check that base glyph exists
          if q in abbreviation_map: base_name = abbreviation_map[q]
          if base_name is None: 
            print('!! %s requires missing glyph %s\n'%(c,q))
      # If base glyph unavailable, use the replacement character <?> with no transformation
      if base_name is None: base_name = transform = "0" 
      base_names += [base_name]
      if base_name!="0": 
        # Mess here, sorry!
        q=inverse_abbreviation_map[base_name]
        mapped_glyphs.add(q)
        if transform !="0": glyphs_isused.add(q)
      transforms += [transform]
    combined = [(b+'|'+t+',').ljust(14) for (b,t) in zip(base_names,transforms)]
    #___________________________________________________________________________
    # How much of the block is mapped?
    first_offset    = -1
    last_offset     = -1
    total_supported =  0
    for i,b in enumerate(base_names):
      if b=="0": continue
      total_supported += 1
      last_offset      = i
      if first_offset<0: 
        first_offset = i
    if first_offset<0 or last_offset<0: 
      blocksource   += '// (none mapped.)'
      missingblocks += [codename]
      continue
    else: 
      blocksource+='// Offsets in %d-%d are mapped.'%(first_offset,last_offset)
    #___________________________________________________________________________
    # Check how sparse the block is. For <=256 characters a sparse list costs 1 
    # byte per item, so stored items cost 1+2 bytes. So cost is N*3. For >256 
    # the cost is n*4.
    supported_range = last_offset - first_offset + 1
    mapdata = '  '
    j = 0;
    sparse = supported_range<=256 and 3*total_supported<2*supported_range
    if sparse: 
      blocksource += '\n// This is a sparse block.'
      issparse    += [codename]
    included = []
    for i in range(first_offset,last_offset+1):
      if sparse and base_names[i]=="0": continue
      if j%8==0: mapdata+='\n  '
      mapdata  += combined[i]
      included += [i]
      j+=1
    if not sparse:
      covered  = {*range(first_offset,last_offset+1)}
      missing  = {i for i in covered if base_names[i]=='0'}
      dense_voids[codename]={chr(i+start) for i in missing}
      isdense += [codename]
    blocksource += mapdata+'\n'
    blocks.append((codename,name,start,stop,first_offset,last_offset,j,blocksource,sparse,included))

#_______________________________________________________________________________
"""
Ok, now we need to consolidate the sparse/dense dispatch code to reduce
redundancy. For this, we need to change the unicode block info to 
contain a single byte: 2 bit flag for NONE/SOFT/DENSE/SPARSE, and 6-bit
index data if needed. The index will lead us to a list of uint16_t offsets
into the codepoint map. Each block also has a start/end. Which I guess will
need to fit into a byte? Hmm. 

[x] block starts
[x] block ends
[x] block data index
[x] sparse data index

I guess.. put sparse blocks at the beginning to simplify. 
"""
SOURCE += '\n'+('/'*80+'\n')*5
SOURCE +=   '////////////////////////////////////////////////////////////////////////////////'
SOURCE += '\n// Datastructure to store base glyph + transform for each mapped block.'
SOURCE += '\n// Each codepoint is associated with a uint16_t. The top TRANSFORMBITS bits'
SOURCE += '\n// encode a transformation code. The bottom CHARBITS store an index to a "base'
SOURCE += '\n// glyph" to be transformed. Index 0 is reserved for "missing glyph", index 1'
SOURCE += '\n// is reserved for "combining diacritics", and index 2 is reserved for SPACE.'
SOURCE += '\n// Some of the transformation codes, those starting with T_EP*, tell the code'
SOURCE += '\n// to pull the glyph from one of the "extended" code-pages of extra glyphs,'
SOURCE += '\n// rather than apply a transform. To save space, unicode blocks with only a few'
SOURCE += '\n// defined glyphs are packed as "sparse". For these, we only store codes for'
SOURCE += '\n// characters that are actually mapped. The `sparse_indecies` array tells us'
SOURCE += '\n// which codepoints within each block are actually mapped, and the '
SOURCE += '\n// `sparse_nmapped` tells us how many are mapped. For a given sparse block,'
SOURCE += '\n// the array `sparse_offsets` tells us where to start reading from '
SOURCE += '\n// `sparse_indecies` to get the list of supported codepoints. Dense blocks '
SOURCE += '\n// store a contiguous range of codepoints, with 0 indicating missing codepoints.'
SOURCE += '\n// Not all dense blocks cover the entire range of the given unicode block.'
SOURCE += '\n// The arrays `first_offsets` and `last_offsets` tell us the subset of each'
SOURCE += '\n// block which is actually mapped, for both sparse and dense blocks. The array'
SOURCE += '\n// `bstart_indecies` tells us where to start reading code data from each block'
SOURCE += '\n// from the `codepoint_map` array.'
SOURCE += '\nstatic const unsigned int codepoint_map[] PROGMEM = {\n'
current_index   = 0
sparse_index    = 0
bstart_indecies = []
first_offsets   = []
last_offsets    = []
sparse_indecies = []
sparse_nmapped  = []
sparse_offsets  = []
# Move sparse blocks to beginning
blocks = [b for b in blocks if b[-2]] + [b for b in blocks if not b[-2]]
for codename,name,start,stop,first_offset,last_offset,j,blocksource,sparse,included in blocks:
  SOURCE += blocksource
  bstart_indecies += [current_index]
  first_offsets   += [first_offset]
  last_offsets    += [last_offset ]
  current_index   += j
  if sparse:
    sparse_offsets  += [sparse_index]
    sparse_indecies += included
    sparse_nmapped  += [len(included)]
    sparse_index    += j
SOURCE += '};\n'
SOURCE += '\n// Blocks have been packed in this order:\n'
SOURCE += '\n'.join(['// %2d %s'%(i,b[1])+('(sparse)' if b[-2] else '') 
  for i,b in enumerate(blocks)])+'\n'
SOURCE += '\n// Starting offset into codepoint_map for each included block:'
SOURCE += pack_array(bstart_indecies,'bstart_indecies')
SOURCE += '\n// Within each included block, offset to first mapped codepoint:'
SOURCE += pack_array(first_offsets,'first_offsets')
SOURCE += '\n// Within each included block, offset to last mapped codepoint:'
SOURCE += pack_array(last_offsets,'last_offsets')
SOURCE += '\n// List which codepoints (relative to start of block) sparse blocks contain:'
SOURCE += pack_array(sparse_indecies,'sparse_indecies')
SOURCE += '\n// Where does included-codepoint list start within sparse_indecies?'
SOURCE += pack_array(sparse_offsets,'sparse_offsets')
SOURCE += '\n// For sparse blocks, how many glyphs are included?'
SOURCE += pack_array(sparse_nmapped,'sparse_nmapped')

################################################################################
print('/'*80+'\n// Interim report')
print('/*')
print('In total, %d out of %d transforms were used'%(NUMBER_OF_TRANSFORMS,MAXNMODS))
print('Voids in dense blocks:')
for codename, voids in dense_voids.items():
  if len(voids): print('  ',codename+':',''.join(sorted(list(voids))))
print('\nThese base glyphs are used:')
print(''.join(sorted(list(mapped_glyphs))))
print('\nThese base glyphs are not used:')
unused = set(canoncode)-mapped_glyphs
print(''.join(sorted(list(unused))))
print('\nAdd the following unicode blocks to use these glyphs:')
for codename,(name,start,stop,_) in get_unicode_blocks_information().items():
    if codename in softmapped: continue
    cc = {chr(i) for i in range(start,stop+1)}
    missing = cc & unused
    if len(missing):
        print(' ',codename+': '+''.join(sorted(list(missing))))
print('\nThese base glyphs are used in transfomed characters:')
print(''.join(sorted(list(glyphs_isused))))
print('\nThese base glyphs are used, but not in in transfomed characters:')
print(''.join(sorted(list(mapped_glyphs - glyphs_isused))))

################################################################################
# Clever code to change how glyph data is packed goes here? 

#_______________________________________________________________________________
# Load character bitmaps from image file
imagefn  = main_glyph_image_filename
fontname = imagefn.split('/')[-1]
fontname = fontname.split('.')[0].lower()
img      = imread(imagefn)
pixelstall, pixelswide, color_channels = img.shape
if not (pixelstall%CH==0): raise ValueError('Image height %d not a multiple of %d pixels'%(pixelstall,CH))
if not (pixelswide%CW==0): raise ValueError('Image width %d not a multiple of %d pixels'%(pixelswide,CW))
# Ignore alpha or any extra channels if present
if color_channels>3: 
    img = img[:,:,:3]
NCOLS  = pixelswide // CW
NROWS  = pixelstall // CH
NCHARS = NCOLS*NROWS
print('\nDetected %d columns' % NCOLS)
print('Detected %d rows'    % NROWS)
# Grab bit values by checking for white pixels
x = np.all(img==1.0,axis=2)[:CH*NROWS,:CW*NCOLS]
# Re-order into a list of HxW characters
u = x.reshape(NROWS,CH,NCOLS,CW).transpose(0,2,1,3).reshape(NCHARS,CH,CW)
u = u[:len(codepoints)]
# We need to flip this upside down for the Arduino
u = u[:,::-1,:]

#_______________________________________________________________________________
# Figure out how much space needed to store each character  (there will be blank
# space on the sides we can remove). Then, find glyphs matching other footprint
# sizes. Maybe we can group glyphs according to their shapes? 
paddings = [*map(get_character_edge_padding,u)]
ca = array(list(canoncode))
def stridxs(s): return ''.join(sorted([ca[i] for i in s]))
unmatched = {*enumerate(paddings)}
padding_groups = []

for q in '⁵₃×agAQfj½':
  q  = aliasmap.get(q,q)[0]
  i0 = canoncode.index(q)
  p0 = paddings[i0]
  L0,R0,B0,T0 = p0
  matched = {(i,(L,R,B,T)) for i,(L,R,B,T) in unmatched if (L>0 and B>=B0 and T>=T0)}
  if len(matched)<=0: continue
  padding_groups+=[(p0,sorted([i for (i,p) in matched]))]
  unmatched -= matched

for q in 'ェぅԱբխॾラ':
  q  = aliasmap.get(q,q)[0]
  i0 = canoncode.index(q)
  p0 = paddings[i0]
  L0,R0,B0,T0 = p0
  matched = {(i,(L,R,B,T)) for i,(L,R,B,T) in unmatched if (B>=B0 and T>=T0)}
  if len(matched)<=0: continue
  padding_groups+=[(p0,sorted([i for (i,p) in matched]))]
  unmatched -= matched
unmatched = [i for (i,p) in unmatched]

for i,(k,v) in enumerate(padding_groups):
  print(i)
  print(k)
  print(''.join([canoncode[i] for i in v]))

# Check something
"""
padding_defined = ''.join([canoncode[i] 
  for _,pg in padding_groups for i in pg])
missing = set(canoncode)-set(padding_defined)
if len(missing):
  raise ValueError('! Somehow the following glyphs didn\'t get'
  ' added to padding groups: %s'%''.join(sorted(list(missing))))
sys.exit(0)
"""

#_______________________________________________________________________________
# All groups divided into glyphs used for transforms and those not
# - "replacement character" broken out as a special case. 
# - "space" broken out as a special case. 
# - "combining mark" broken out as a special case
# Build a binary search tree. For each grouping we need to know
# - start, end glyph index
idx_used = {i for (i,c) in enumerate(canoncode) if c in glyphs_isused}
print('Reminder: %d glyphs are used in transformations'%len(glyphs_isused))
print('Reminder: %d transformations defined'%NUMBER_OF_TRANSFORMS)
remove = {canoncode.index(c) for c in '� '}
reordered = ''
groupinfo = []
blockdata = []
paddings  = array(paddings)
def add_glyph_group(s):
  global reordered, groupinfo, blockdata
  if not len(s): return
  s = stridxs(s)
  print('Group %d:'%len(groupinfo),s)
  # We need to figure out how to pack this group. Each group needs: start 
  # index, number of glyphs, row start, col start, nrows, ncols
  ii = int32([canoncode.index(c) for c in s])
  L,R,B,T    = np.min(paddings[ii],axis=0)
  rowstart   = T
  colstart   = L
  nrows      = CH-B-rowstart
  ncols      = CW-R-colstart
  # Patch for now in case we encounter an empty space
  if nrows<0:
    rowstart = colstart = 0
    nrows = 0
    ncols = 0
    L = 0
    T = 0
    B = CH
    R = CW
  nglyph     = len(ii)
  gstart     = len(reordered)
  groupinfo += [(gstart,nglyph,rowstart,nrows,colstart,ncols)]
  rowdata    = concatenate([u[i][T:CH-B,L:CW-R] for i in ii],axis=1)
  print(shape(rowdata))
  rowdata    = array([bitpack_row(d) for d in rowdata]).T
  blockdata += [rowdata]
  reordered += s

# Prepare bitmap groups; '�' ' ' handled as ad-hoc patches for now. 
add_glyph_group({canoncode.index('�')})
add_glyph_group({canoncode.index(' ')})

for (L0,R0,B0,T0),fit in padding_groups: 
  add_glyph_group((set(fit) - remove) & idx_used)
add_glyph_group((set(unmatched) - remove) & idx_used)

# By now all used indecies should be mapped
if len(reordered)>MAXNCHAR-2:
  print('REORDERED:',reordered)
  raise ValueError(('No more than %d characters can be used as base glyphs,'
  ' but there are %d base glyphs!')%(MAXNCHAR-2,len(reordered)))

for (L0,R0,B0,T0),fit in padding_groups: 
  add_glyph_group((set(fit) - remove) - idx_used)
add_glyph_group((set(unmatched) - remove) - idx_used)

for i in idx_used:
  if not canoncode[i] in reordered:
    print(reordered)
    raise ValueError('! Glyph for %s is not packed'%canoncode[i])


SOURCE += '\n'+('/'*80+'\n')*5
SOURCE +=   '////////////////////////////////////////////////////////////////////////////////'
SOURCE += '\n// Packed glyph bitmap data'
SOURCE += '\n// We store glyphs in a collection of bitmaps. Each bitmap is associated with'
SOURCE += '\n// a group of glyphs of a given size. For example, upper case and lower case'
SOURCE += '\n// letters are stored in separate bitmaps. Each bitmap concatenates glyphs'
SOURCE += '\n// horizontally, into a short, fat image that contains a single row of'
SOURCE += '\n// characters. Each row of pixels is then packed as a bit vector, and the bit'
SOURCE += '\n// vectors for each row are interleaved. The packed bitmap data for each group'
SOURCE += '\n// are then concatenated. To find the correct bitmap of a given glyph index,'
SOURCE += '\n// `group_bitmap_offsets` will tell you where in `bitmap_data` each bitmap'
SOURCE += '\n// starts. `group_startidx` tells you the starting glyph index for each group.'
SOURCE += '\n// `group_nglyphs` tells you the number of glyphs in each group. The arrays'
SOURCE += '\n// `group_rowstart`, `group_nrow`, `group_colstart`, `group_ncol` indicate'
SOURCE += '\n// where within the 6x12 character the glyph bitmap should be drawn. (Most glyph'
SOURCE += '\n// bitmaps do not store the full 6x12 image, there is a lot of empty space.)'
SOURCE += '\n#define NGLYPHS (%d)'%len(reordered)
SOURCE += '\n#define NGROUPS (%d)'%len(groupinfo)
start_index = 0
start_idxs  = []
all_bitmap_data = []
for ib,bd in enumerate(blockdata):
  all_bitmap_data.extend(bd.ravel())
  start_idxs  += [start_index]
  start_index += len(bd.ravel())
SOURCE += pack_array(all_bitmap_data,'bitmap_data')
SOURCE += '\n// Index into bitmap_data for each group of glyph bitmaps'
SOURCE += pack_array(start_idxs,'group_bitmap_offsets')
# Add arrays that contain information for how to find glyphs in each group
gstart,nglyph,growstart,ngrows,gcolstart,ngcols = array(groupinfo).T
SOURCE += '\n// Starting glyph index for each group of glyph bitmaps'
SOURCE += pack_array(gstart   ,'group_startidx')
SOURCE += '\n// Number of glyphs in each group of glyph bitmaps'
SOURCE += pack_array(nglyph   ,'group_nglyphs' )
SOURCE += '\n// Starting row of glyph bitmap for each group'
SOURCE += pack_array(growstart,'group_rowstart')
SOURCE += '\n// Number of rows in bitmap for each group'
SOURCE += pack_array(ngrows   ,'group_nrow'    )
SOURCE += '\n// Starting column of bitmap for each group'
SOURCE += pack_array(gcolstart,'group_colstart')
SOURCE += '\n// Nuber of columns in bitmap for each group'
SOURCE += pack_array(ngcols   ,'group_ncol'    )
# C routine to unpack this data
SOURCE += '''
/*
Character bitmap data is sent to the screen from left to right, bottom to top:
                              ...
                              VWXYZa
                              PQRSTU
                              JKLMNO
                              DEFGHI
                              789ABC
                              123456

Internally, each row is a packed in a byte. The left-most column is the 
lowest-order bit. The top two bit are not used. The bottom row is "0". So the 
above pixel layout would have the following bit-packing:

                               76543210 Bit
                          Byte |      |
                          0 -> xx654321
                          1 -> xxCBA987
                          2 -> xxIHGFED
                          3 -> xxONMLKJ
                          4 -> xxUTSRQP
                          5 -> xxaZYXWV
                          ...


It's easier to think about this by listing the lowest-order bit first:

                               01234567 Bit
                          Byte |      |
                          0 -> 123456xx
                          1 -> 789ABCxx
                          2 -> DEFGHIxx
                          3 -> JKLMNOxx
                          4 -> PQRSTUxx
                          5 -> VWXYZaxx
                          ...

For character bitmaps, empty space above/below/left/right of the character
is removed. Characters are then concatenated horizontally. Each row of pixels
in this concatenated bitmap is packed into a bit vector in a way that is 
(relatively) easy to unpack. 

bitpack_row: This function takes a row of pixels, chops it up into groups of 8,
and packs these into 8-bit integers, with the leftmost pixels occupying lower-
order bits

Each row of the image is packed like this. The order of the rows are then
reversed to convert between the normal top-to-bottom ordering of pixels and
the bottom-to-top packing that we use on the Arduino. 

Sometimes, glyph bitmap data ends up split across a byte boundary, for example: 

                                  567.012 Bit
                        Row       |     |
                        0 -> xxxxx123 456xxxxx
                        1 -> xxxxx789 ABCxxxxx
                        2 -> xxxxxDEF GHIxxxxx
                        3 -> xxxxxJKL MNOxxxxx
                        4 -> xxxxxPQR STUxxxxx
                        5 -> xxxxxVWX YZaxxxxx
                              BYTE0    BYTE1

Can we grab these by reading a whole word? Possibly? AVR is little-endian.
Higher-order bytes of a uint16 are in higher addresses. So this won't work. 
It might work if we reversed the bit-packing order, but then.. no, too 
confusing. We could possibly write a custom macro to load a big-endian uint8, 
but also too confusing. 


*/

/**
 * Load a glyph from memory. Assumes glyphs have been horizontally concatenated
 * into a single bitmap, each row packed in a bit-vector, and all rows
 * interleaved into a single array. Low-order bits correspond to the left-
 * most columns of pixel data.
 * 
 */
inline void load_rowpacked_glyph(const byte *c, 
  unsigned int index, 
  byte rowstart, byte nrows,
  byte colstart, byte ncols ) {
  
  // Start by zeroing out empty rows
  
  byte r=0;
  while (r<rowstart) { char_bitmap[r]=0; r++; }
  
  // - Get the size of the character. Rows are packed separately, so the 
  //   "stride" between consecutively packed bytes equals the number of rows. 
  // - To find the start of character data, take the number of columns (in 
  //   bits), times the index. 
  // - From this, calculate the byte to start reading at (÷8), and the offset
  //   (%8; in bits) into this byte.
  // - Then, to figure out where to start: multiply byte index by array stride.
  
  int         bit_index  = index * ncols;
  int         byte_index = bit_index >> 3;
  byte        bit_offset = bit_index & 0b111;
  const byte *read_head  = c + byte_index * nrows;
  
  // If the bit offset + character width is more than 8, row data will be
  // split across multiple bytes.
  
  byte  is_split   = (bit_offset + ncols) > 8;
  
  // Read rows from memory one at a time. Shift the bits as needed.
  // Now, each row will be read from memory. How though? Stride is the number 
  // of packed rows. And we can advance one byte at a time if we've packed this
  // right. The "bitstart" is the thing to worry about. If that bitstart + 
  // ncols is less than 8, then we only need to read one byte. Otherwise, we
  // might be split across a byte boundary.
  
  byte rowstop = rowstart + nrows;
  
  // Mask to delete out-of-bounds pixel data
  byte bitmask = (1<<ncols)-1;
  
  // current cost is 114
  while (r<rowstop) { 
  
    byte row_data = ((byte)pgm_read_byte(read_head)) >> bit_offset;
    
    // Get second byte if needed
    if (is_split) row_data |= ((byte)pgm_read_byte(read_head+nrows)) << (8-bit_offset);
    
    // Shift into place and store in the character bitmap register
    char_bitmap[r] = (row_data&bitmask) << colstart;
    
    r++;
    read_head++;
  }
  // Clear any remaining rows
  while (r<CH) { char_bitmap[r]=0; r++; }
}

/**
 * Load glyph data based on glyph index.
 */
byte load_glyph_bitmap(unsigned int i) {
  int found = binary_search_range(i,NGROUPS,group_startidx,group_nglyphs);
  if (found<0) return NOT_IMPLEMENTED;
  unsigned int offset = pgm_read_word(group_bitmap_offsets + found);
  load_rowpacked_glyph(bitmap_data+offset, i - pgm_read_word(group_startidx +found),
    pgm_read_byte(group_rowstart +found), pgm_read_byte(group_nrow +found),
    pgm_read_byte(group_colstart +found), pgm_read_byte(group_ncol +found));
  return LOADED;
}

/*
Note on timing: 

2883 ms to draw all glyphs from scratch

after I removed
binary_search_range(i,NGROUPS,group_startidx,group_nglyphs);
//Serial.println(found);
it took 253, why is that?

//Serial.println(found); must take a very long time!

After hiding the cursor, time taken is 198
Drawing the cursor must take 253 - 198 = 55 ms
Maybe you can speed this up: instead of using xor, save the pixel data
behind the cursor? 

After moving load_glyph_bitmap out of the loop, we get 149 ms
meaning bitmap loading takes 198 - 149 = 49 ms. 
not the majority of the time taken, but not zero either. 

A loop with just `drawStyledChar` takes 139, 10 ms less. So cursor 
updating takes 10ms. That seems a bit high to me? I guess this includes
loop iteration overhead and time requires to get the time. Yes, it takes
12 ms just to update the cursor. This is probably real, since a loop contianing
just DELAY1 takes just 1 millisecond. 

`prepare_cursor` alone seems to take 1ms
`advance_cursor(1);` alone takes 1ms
But combine them and you get 12 ms. 

Maybe it's the newline that's slowing things down? That doesn't quite make
sense though, nothing happens in `newline` is we don't need to scroll. 
Time goes down to 3 ms if we remove the updates to the "blink state" bit
vector, so this might be slowing things down. 
After optimizing `update_blink` it takes 8 ms. So, not great. Blink code
updates still cost 5ms. Well, update_blink is called from only one place, 
so at least inlining shaves off another 1ms here. 
Then it looks like `drawStyledChar` is taking 144-7 = 137 ms on its own. 

Can we get this down? 
Unpacking the macro leaves the same time (good, expected). 
all but 4ms seems to be used by blit_rowwise, can this be improved? 
Passing char_bitmap as a fixed global saves 1ms. 

Ok aggressive loop unrolling saves the day. For now.




*/
'''

#_______________________________________________________________________________
'''
blocks in order
compute codes
soft, missing, dense, sparse
'''
################################################################################
# Declare handling routine for each block
# Also determine starting/ending ranges for each block
SOURCE += '\n'+('/'*80+'\n')*5
SOURCE +=   '////////////////////////////////////////////////////////////////////////////////'
SOURCE += '\n// Unicode block-mapping table'
SOURCE += '\n// The following unicode blocks are supported. Softmapped blocks are associated'
SOURCE += '\n// with a custom function which must be implemented separately. All other blocks'
SOURCE += '\n// are handled through the mapping table defined above\n\n'
supported_blocks = mapped_blocks + softmapped
blockinfo = get_unicode_blocks_information()
starts, lengths, fn_names = [],[],[]
for shortname,(name,start,stop,nassigned) in blockinfo.items():
    if not shortname in supported_blocks: continue
    length = stop - start + 1
    if length//16>0xff:
        raise ValueError('Block %s is too long to use'%name)
    assert start %16==0
    assert length%16==0
    if shortname in softmapped:
      SOURCE += 'int _%s(uint16_t c); // 0x%08X-0x%08X\n'%(shortname,start,stop)
    else:
      SOURCE += '// %s 0x%08X-0x%08X (handled via mapping table)\n'%(shortname,start,stop)
    starts.append(start//16)
    lengths.append(length//16)
    fn_names.append('_'+shortname)
starts  = array(starts)
lengths = array(lengths)
SOURCE += '\n'
SOURCE += '// Number of blocks defined\n'
SOURCE += '#define NBLOCKS (%d)\n'%len(lengths)
SOURCE += '\n// Starting unicode point of each defined block, divided by 16'
SOURCE += pack_array(starts, 'block_starts_x16')
SOURCE += '\n// Number of codepoints in each block, divided by 16'
SOURCE += pack_array(lengths,'block_lengths_x16')
SOURCE += '\n// Last supported row in unicode tables\n'
SOURCE += '#define LASTROW (0x%X)\n'%((starts+lengths)[-1]-1)
SOURCE += '\n// Codes to describe how each mapped unicode block is supported:\n'
SOURCE += '#define MISSING (0)\n'
SOURCE += '#define SOFT    (1)\n'
SOURCE += '#define DENSE   (2)\n'
SOURCE += '#define SPARSE  (3)\n\n'
SOURCE += '// Packed data describing each block;\n'
SOURCE += '// Low 2 bits indicates block type, as above\n'
SOURCE += '// Remaining bits tells us where to find more information'
supported_blocks = mapped_blocks + softmapped
includedblocks = [b[0] for b in blocks]
blockcodes = []
for shortname,(name,start,stop,nassigned) in blockinfo.items():
    if not shortname in supported_blocks: continue
    code = index = None
    if   shortname in missingblocks: 
      code = 0
      index = 0
    elif shortname in softmapped:
      code = 1
      index = softmapped.index(shortname)
    elif shortname in isdense:
      code = 2
      index = includedblocks.index(shortname)
    elif shortname in issparse: 
      code = 3
      index = includedblocks.index(shortname)
    else: 
      assert 0
    blockcodes += [index*4 + code]
SOURCE += pack_array(blockcodes,'blockcodes')
SOURCE += '\n// For DENSE and SPARSE blocks, the index code provides the offset into the'
SOURCE += '\n// bstart_indecies, first_offsets, last_offsets, sparse_offsets, and '
SOURCE += '\n// sparse_nmapped arrays. For SOFT blocks, the index is an offset into the '
SOURCE += '\n// following array of function pointers:'
line = '\nstatic int(*const softmap_functions[])(uint16_t) = {'
print(softmapped)
for b in softmapped:
  fn_name = '_'+b+','
  print(fn_name)
  if len(line+fn_name)>80:
    SOURCE += line+'\n'
    line = '  '
  line += fn_name
SOURCE += line + ('\n' if len(line+'};')>80 else '') + '};\n\n'
SOURCE += '''
/*
To read unicode data, 
*/

////////////////////////////////////////////////////////////////////////////////
/* Load unicode glyph (with transform) from mapping table
*/
int handle_unicode_mapping_table(byte blocktype, byte i, byte c) {

  // Check that c is within the mapped range
  byte first = pgm_read_byte(first_offsets+i);
  byte last  = pgm_read_byte(last_offsets +i);
  
  //Serial.print("Code relative offset: ");
  //Serial.println(c);
  //Serial.print("First mapped offset: ");
  //Serial.println(first);
  //Serial.print("Last mapped offset: ");
  //Serial.println(last);
  
  if (c<first || c>last) return NOT_IMPLEMENTED;

  int found;
  if (blocktype==SPARSE) {
  
    // For sparse blocks, we need to get the mapped range (this part is the same
    // as with dense blocks). Then, we need to look up how many glyphs are
    // mapped and which glyphs are mapped.
    // How many glyphs are mapped? 
    byte N = pgm_read_byte(sparse_nmapped + i);
    //Serial.print("Sparse; Number of mapped glyphs: ");
    //Serial.println(N);
    
    // Where can I find the list of which glyphs are mapped? 
    unsigned int sidx_offset = pgm_read_word(sparse_offsets + i);
    //Serial.print("sidx_offset: ");
    //Serial.println(sidx_offset);
    
    // What is the search key I should use to look up this codepoint?
    unsigned int index = c;// - first;
    //Serial.print("index: ");
    //Serial.println(index);
    
    // Search for index in the sorted list at sparse_indecies + sidx_offset
    // of length N. If not found, return.
    found = binary_search(index, N, sparse_indecies + sidx_offset);
    //Serial.print("found: ");
    //Serial.println(found);
    if (found==0xff) return NOT_IMPLEMENTED;
  } else {
    found = c - first;
  }
  
  // figure out where the data for this block start
  unsigned int cindex = pgm_read_word(bstart_indecies + i);
  
  //Serial.print(" found offset : ");
  //Serial.println(found);
  
  uint16_t glyphtransform = pgm_read_word(codepoint_map + cindex + found);
  
  //Serial.print("Packed code: ");
  //Serial.println(glyphtransform);
  
  // Obtain the code 
  return handle_transform(glyphtransform);
}



////////////////////////////////////////////////////////////////////////////////
/** Dispatch unicode point to subroutines for handling various blocks and 
 *  range of codepoints.
 */
int load_unicode(uint32_t code) {

  //Serial.print("Code ");
  //Serial.println(code);

  // Divide code by 16 to get its "row" in the uncode table
  unsigned int coderow = code>>4;
  // Skip codepoints past the end of the mapped blocks
  if (coderow>=LASTROW+1) return NOT_IMPLEMENTED;
  // Binary search to find function to handle this block
  int found = binary_search_range(coderow, NBLOCKS, block_starts_x16, block_lengths_x16);
  
  //Serial.print("Block info index ");
  //Serial.println(found);
  
  if (found<0) return NOT_IMPLEMENTED;
  // We now have the index of the block required to handle this code-point
  // Look up where this block starts to convert out codepoint into an offset
  // relative to the start of this unicode block. 
  unsigned int block_start_row = pgm_read_word(&block_starts_x16[found]);
  code -= block_start_row*16;
  
  // Previously, we handled each block as its own function. This wasted space
  // return (*unicode_block[found])(code - block_start_row*16);
  // Now, we handle blocks differently based on whether they are soft-mapped
  // vs. mapped as a base-glyph + transform. 
  // Get block information
  byte blockcode = pgm_read_byte(blockcodes + found);
  byte blocktype = blockcode & 0b11;
  byte blockidx  = blockcode >> 2; 
  
  //Serial.print("Block type ");
  //Serial.println(blocktype);
  //Serial.print("Block index ");
  //Serial.println(blockidx);
  
  switch (blocktype) {
    case MISSING: return NOT_IMPLEMENTED;
    case SOFT:    return (*softmap_functions[blockidx])(code);
  }
  return handle_unicode_mapping_table(blocktype, blockidx, code);
}

////////////////////////////////////////////////////////////////////////////////
/** Parse utf-8 encoded unicode codepoint. Based on the first byte, this will
 *  attempt to read up to 3 more bytes from the serial input. If a valid 
 *  unicode sequence is found, it will attempt to interpret and draw the 
 *  corresponding character. Returns FAIL if an invalid utf-8 sequence 
 *  encountered, or if there was an error in rendering the unicode point. If it
 *  cannot render the given unicode point, the replacement character <?> should
 *  be rendered instead. 
 *  @param byte1: first byte of a putative unicode sequence (we'll wait for 
 *      more if needed)
 */
int parse_utf8(byte byte1) {
  uint32_t code = byte1;
  if (byte1>=128) {
    int nbytes = 0;
    if      ((byte1>>5)==0b110  ) {code=byte1 & 0b11111; nbytes=1;}
    else if ((byte1>>4)==0b1110 ) {code=byte1 &  0b1111; nbytes=2;}
    else if ((byte1>>3)==0b11110) {code=byte1 &   0b111; nbytes=3;}
    if (!nbytes) return FAIL; // Ignore bad utf-8
    for (int j=0; j<nbytes; j++) {
      byte b = blocking_read();
      if (!((b>>6)==0b10)) return FAIL; // Ignore bad utf-8
      code = (code<<6)|(b&0b111111);}
  }
  //pause_incoming_serial();
  prepare_cursor();
  byte return_code = load_unicode(code);
  if (return_code == LOADED) {
    // Soft-fonts draw, but mapped fonts only load the character bitmap.
    // This allows the mathematical alphanumerics soft-font to re-use the
    // unicode mapping for Greek, without drawing to screen, in order to
    // further style characters before drawing. 
    drawStyledChar();
    advance_cursor(1);   
    return SUCCESS;
  }
  else if (return_code != SUCCESS) {
    //load_and_draw_glyph(REPLACEMENT_CHARACTER);
    load_glyph_bitmap(REPLACEMENT_CHARACTER);
    drawCharFancy(CH*row,CW*col,fg,bg,NORMAL,NORMAL,HALFWIDTH);
    advance_cursor(1);
  }
  return return_code;
}
'''

################################################################################
################################################################################
################################################################################
################################################################################
# Save glyph codes;
# Need to tweak "extended" codes
CODESOURCE += '\n\n'+'/'*80+'\n'
CODESOURCE += '// Indecies for various glyphs "G_" into the bitmap code page\n'
CODESOURCE += '#define %s (%3d) // Code to support aliasing combining marks'%\
  ("_COMB_".rjust(7),1)+'\n'
for ii,c in enumerate(reordered):
    if not c in base_glyphs_used: continue
    c = aliasmap.get(c,c)[0]
    if not c in abbreviation_map or abbreviation_map[c] is None:
        print(abbreviation_map)
        raise ValueError('!! (prepare_unicode_mapping): %s has no abbreviation'%c)
    shortname = abbreviation_map[c]
    longname  = codepoint_names[c][1]
    # 0: used to indicate null
    # 1: used to indicating combining diacritic
    # 2: start counting actual glyphs at 2
    idx = ii+1
    if idx<MAXNCHAR:
      CODESOURCE+='#define %s (%3d) // 0x%08X %s'%\
        (shortname.rjust(7),idx,ord(c),longname.lower())+'\n'
    else:
      # Code point lies in one of the extended/extra "pages"
      page = int(ceil(((idx+1)/MAXNCHAR)))
      idx %= MAXNCHAR
      CODESOURCE+='#define %s (%3d|T_EP%d) // 0x%08X %s'%\
        (shortname.rjust(7),idx,page,ord(c),longname.lower())+'\n'
      
      
################################################################################
################################################################################
################################################################################
################################################################################
# Write header files
SOURCE     += '\n\n#endif // %s\n'%headername    
CODESOURCE += '\n\n#endif // %s\n'%codeheadername
with open(unicode_mapping_filename,'wb') as f: f.write(SOURCE    .encode('utf8'))
with open(glyphcodes_filename     ,'wb') as f: f.write(CODESOURCE.encode('utf8'))

#_______________________________________________________________________________
print('\nGlyph packing order:')
print(reordered)

#_______________________________________________________________________________
# Enclosed alphanumerics code will need to be able to find these
for c in enclosed_alphanumerics_base_glyphs:
  if not c in reordered:
    raise ValueError('Base glyph %s for enclosed alphanumerics missing'%c)
print('\n// Glyph indecies for for enclosed alphanumerics; 0-20 a-z A-Z'+
  pack_array(array([reordered.index(c)\
    for c in enclosed_alphanumerics_base_glyphs]),
  'enclosed_map'))
for c in mathematical_alphanumerics_base_glyphs:
  if not c in reordered:
    raise ValueError('Base glyph %s for mathematical alphanumerics missing'%c)
print('\n// Glyph indecies for for mathematical alphanumerics; AZa𝚤 𝚥AΩ𝛁αω𝜕𝜖𝜗𝜘𝜙𝜚𝜛'+
  pack_array(array([reordered.index(c)\
    for c in mathematical_alphanumerics_base_glyphs]),
  'alphanumerics_map'))

#_______________________________________________________________________________
# Map the half-width Kana onto Katakana (or other ad-hoc replacements)
halffullequivalence = [
  '｡o', '｢[', '｣]', '､,', '･・', 'ｦヲ', 'ｧァ', 'ｨィ', 'ｩゥ', 'ｪェ',
  'ｫォ', 'ｬャ', 'ｭュ', 'ｮョ', 'ｯッ', 'ｰー', 'ｱア', 'ｲイ', 'ｳウ',
  'ｴエ', 'ｵオ', 'ｶカ', 'ｷキ', 'ｸク', 'ｹケ', 'ｺコ', 'ｻサ', 'ｼシ',
  'ｽス', 'ｾセ', 'ｿソ', 'ﾀタ', 'ﾁチ', 'ﾂツ', 'ﾃテ', 'ﾄト', 'ﾅナ',
  'ﾆニ', 'ﾇヌ', 'ﾈネ', 'ﾉノ', 'ﾊハ', 'ﾋヒ', 'ﾌフ', 'ﾍヘ', 'ﾎホ',
  'ﾏマ', 'ﾐミ', 'ﾑム', 'ﾒメ', 'ﾓモ', 'ﾔヤ', 'ﾕユ', 'ﾖヨ', 'ﾗラ',
  'ﾘリ', 'ﾙル', 'ﾚレ', 'ﾛロ', 'ﾜワ', 'ﾝン', 'ﾞ゛', 'ﾟ゜']
halffullmap = [ord(pair[1]) for pair in halffullequivalence] 
print('\n// Unicode points for half-width kana substitutes:'+
  pack_array(halffullmap,'halffullmap'))


#_______________________________________________________________________________
# Prepare special line to have soft-mapped geometricsymbols route back to the
# table-mapped geometricsymbols. Just need index for geometrixsymbols
# Also assume this block is SPARSE (3)

print('  // Hand-coded to fall back to mapped version of geometric shapes')
print('  return handle_unicode_mapping_table(3, %d, c);'%\
    [b[0] for b in blocks].index('geometricshapes'))





#_______________________________________________________________________________
# Prepare an output image of the new glyph ordering for references
ncols = 32*2
nrows = max(16,int(ceil(len(canoncode)/ncols)))
reordered_image = zeros((nrows*CH,ncols*CW))
i = 0
for c in reordered:#sorted(canoncode):
  row = i//ncols
  col = i%ncols
  reordered_image[row*CH:(row+1)*CH,col*CW:(col+1)*CW] = u[canoncode.index(c)][::-1,:]
  i += 1
figure("Re-ordered glyph packing",figsize=(1*2,2*2*nrows/ncols),dpi=(32*6)*2)
imshow(reordered_image,interpolation='nearest',cmap='bone_r'); 
subplots_adjust(0,0,1,1,0,0);
axis('off')
draw()
print('(You might need to close any opened Matplotlib windows or press Control+C to end this program)')
print('*/')
show()











