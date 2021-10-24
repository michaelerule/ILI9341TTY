#!/usr/bin/env python3
"""
Prepare the header file which defines the main font data

TODO

- Characters are defined if they are used in the mapping
- Transformations are defined only if they are used in the mapping
- A warning is given for glyphs that are never used
- A warning is given for transformations that are never used
"""

from pylab import *
import unicodedata
from CONFIG         import *
from font_utilities import *

C_SOURCE   = ''
headername = unicode_mapping_filename.split('/')[-1].split('.')[0].upper()
C_SOURCE += "#ifndef %s_H\n"%headername
C_SOURCE += "#define %s_H\n"%headername
C_SOURCE += '// This file is automatically generated, do not edit it,\n'
C_SOURCE += '// see ./prepare_fonts/README.md for more information. \n'
C_SOURCE += '\n'
C_SOURCE += '#include "%s"'%diacritics_filename.split('/')[-1]
C_SOURCE += '\n'
C_SOURCE += '// geometricshapes handles some glyphs as semigrahics\n'
C_SOURCE += '#include "softfonts.h"\n'

# Load glyph mapping
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

# Check that codepoints are formatted as we expect
assert all([len(l)<=32 for  l in codepoints])
codepoints = ''.join(codepoints)
print(len(codepoints),len(codepoints)/32)
        
# Make sure ASCII glyphs stay at their ASCII index!
for c in ASCII:  assert codepoints[ord(c)]==c

# Load glyph alias information
aliases = []
with open(glyph_aliases_filename,'r') as f:
    for line in f.readlines():
        line = line.replace('\n','')
        aliases.append(sorted(list(set(line))))
aliasmap = rebuild_aliasmap(aliases, codepoints)

# Convert all code points to their lowest alias
new_codepoints = ''
for ic,c in enumerate(codepoints):
    if c==' ': 
        new_codepoints+=' '
        continue
    a = aliasmap.get(c,c)[0]
    if a in new_codepoints:
        print('Row %d Column %d; %s'%(ic//32,ic%32,c))
        raise ValueError('character %s with alias %s (%x) is aleady mapped'\
            %(c,a,ord(a)))
    new_codepoints+=a
    
# Generate abbreviations for glyphs that are not ASCII
abbreviation_map = {}
codepoint_names  = []
for ii,c in enumerate(new_codepoints):
    c = aliasmap.get(c,c)[0]
    shortname, name = generate_codepoint_name_abbreviation(c, aliases, abbreviation_map)
    codepoint_names.append((shortname, name))

# Get transformation commands, their names, and abbreviations
execfile(transform_commands_filename, globals())

# Ensure there are no duplicate abbreviations and add the "long name" to
# the python namespace so that character decompositions can refer to it
command_dictionary = {}
for i,(shortname,(longname,csourcecode)) in enumerate(commands):
    if shortname in command_dictionary:
        raise ValueError(('Command %d (%s): '
                         'The abbreviation %d is already used for %s')\
        %(i,longname,shortname,command_dictionary[shortname]))
    command_dictionary[shortname] = (longname,csourcecode)
    globals()[longname]=shortname
commands = command_dictionary

# Load character decomposition information
# This represents unicode characters as a base glyph + transformation
execfile(character_decompositions_filename, globals())

# Ensure decomposed characters represented in terms of canonical alias
newdecompose = {}
for k,v in decompose.items():
    k = aliasmap.get(k,k)[0]
    if len(v)<2: continue
    base = v[0]
    base = aliasmap.get(base,base)[0]
    transform_command = v[1:].upper()
    if not transform_command in commands: continue
    newdecompose[k] = base+transform_command
decompose = newdecompose

# Load information on unicode blocks (pulled from Wikipedia), removing blocks
# that aren't implemented via unicode-point mapping.
blockinfo = get_unicode_blocks_information()
blockinfo = {k:v for (k,v) in blockinfo.items() if k in mapped_blocks}

# Determine which characters are potentially mapped
mapped = set()
for shortname,(name,start,stop,nassigned) in blockinfo.items():
    for i in range(start,stop+1):
        c = chr(i)
        try:
            name = unicodedata.name(c)
            mapped.add(c)
        except ValueError:
            continue

# Check all characters and how each one is defined
# Check which base characters and transforms are actually used
base_glyphs_used    = set()
transforms_required = set()
missing_bases       = set()
undefined_chars     = []
for ch0 in mapped: 
    # ASCII is supported by default
    if ch0 in ASCII: continue
    # Convert to canonical alias if one exists
    ch = aliasmap.get(ch0,ch0)[0]
    # Is it supported as a base glyph?
    if ch in new_codepoints:
        base_glyphs_used.add(ch)
    # Is it supported as a transformed glyph
    elif ch in decompose:
        d = decompose[ch]
        base_glyph = aliasmap.get(d[0],d[0])[0]
        transform  = d[1:]
        # Transform will only be used if the required base glyph exists
        if base_glyph in new_codepoints:
            base_glyphs_used.add(base_glyph)
            transforms_required.add(transform)
        else:
            undefined_chars.append(ch0)
            missing_bases.add(ch0)
    else:
        undefined_chars.append(ch0)

# Print out some reporting information
#print('')
#print('PREPARE_UNICODE_MAPPING: These codepoints are mapped but not defined:')
#print(' '.join(undefined_chars))
print('')
print('PREPARE_UNICODE_MAPPING: These glyphs are defined but never used:')
unused_glyphs = set(new_codepoints) - base_glyphs_used - set(ASCII)
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

'''
Variant to focus on wasted space. For each block, get mapped points. 
Get lowest and highest mapped point. 
Get all unmapped points between these.
'''

# Determine which characters are potentially mapped
undefined_chars = set(undefined_chars)
print('PREPARE_UNICODE_MAPPING: Wasted space in each block due to undefined characters:')
for shortname,(name,start,stop,nassigned) in blockinfo.items():
    charsinthisblock = {chr(i) for i in range(start,stop+1)}
    undefinedinblock = charsinthisblock & undefined_chars
    definedinblock   = charsinthisblock - undefinedinblock
    definedidxs      = sorted([ord(c) for c in definedinblock])
    if len(definedidxs)<=0: continue
    definedstart = definedidxs[0]
    definedstop  = definedidxs[-1]
    definedrange = {chr(i) for i in range(definedstart,definedstop+1)}
    missingindefinedrange = definedrange & undefinedinblock
    if len(missingindefinedrange)<=0: continue
    print(name+': '+' '.join(sorted(list(missingindefinedrange))))

print('')
print('(Note: wasted space could be fixed by switching to a sparse mapping for sparsely-supported block; Features to add later?)')

'''
How to do this: 

For each block store the number of supported characters and 
a sorted list of supported characters. Binary search to find the character
index, then pull the base glyph + transform code from a buffer with
empty characters removed. 

This will likely require an extra 2 bytes of storage per character so only
makes sense for blocks that are more than half empty. Or two-thirds full if
the block has <256 chars and we can get away with one byte.
'''

# remove unused commands from commands.items()
for t in unused_transforms:
    del commands[t]

# Verify that all used base glyphs exist
# And that all base glyphs are defined
assert len(base_glyphs_used)==len(base_glyphs_used&set(new_codepoints))
assert len(base_glyphs_used - set(new_codepoints))==0

# TODO: 
# Figure out which transforms can be supported by a call out to the diacritics
# Bulid an index to map these without using the switch block

################################################################################
# Start of source code

# Define abbreviations for glyphs that are not ASCII
C_SOURCE+='\n\n'+'/'*80+'\n'
C_SOURCE+='// Indecies for various glyphs "G_" into the bitmap code page\n'
for ii,c in enumerate(new_codepoints):
    if not c in base_glyphs_used: continue
    if c in ASCII: continue
    c = aliasmap.get(c,c)[0]
    if not c in abbreviation_map or abbreviation_map[c] is None:
        print(abbreviation_map)
        raise ValueError('!!ERROR (prepare_unicode_mapping): Character %s has no defined abbreviation'%c)
    shortname = abbreviation_map[c]
    longname  = codepoint_names[ii][1]
    C_SOURCE+='#define %s (%3d) // 0x%08X %s'%(shortname.rjust(7),ii,ord(c),longname.lower())+'\n'

# Some transformations (reflections) call out to subroutines
# Define any new subroutines in <transform_subroutines_filename>.
# They are added to the source code here. 
C_SOURCE+='\n'+'/'*80
C_SOURCE+=''.join(open(transform_subroutines_filename,'r').readlines())
C_SOURCE += '\n'

# Define abbreviated names of each transformation. These are used in the 
# generated mapping tables in the C source code. 
C_SOURCE+=('/'*80+'\n// Transformation command codes:\n')
i = 1
for abbreviation, description in commands.items():
    if isinstance(description,tuple):
        # Transform code exists
        description = description[0]
    C_SOURCE+=('#define %s%s (%3d) // %s'%(transform_code_prefix,
                                           abbreviation.ljust(3),
                                           i*MAXNCHAR,
                                           description))+'\n'
    i+=1
    
# Make sure we have enough bits to encode all transform codes!
assert i<MAXNMODS

# Start of the function to handle transformation code
C_SOURCE+=('\n'+'/'*80+'\n'+"""\
/** Many characters can be formed by transforming others.
 *  This routine accepts a "command" byte and an "index" byte. 
 *  The "index" specifies a base glyph, and the "command" specifies some way to
 *  transform this glyph.
 *  @param index: index into the character bitmap
 *  @param command: command code to transform it
 */
int handle_transform(unsigned int transform_code) {
  unsigned int base_character = transform_code &  %s;
  unsigned int command        = transform_code &  %s;        
  // Load base glyph into memory
  load_glyph_bitmap(base_character);
  // Apply transformation command
  switch (command) {
      case 0: break; // No transform\n""")%(CHARMASK,COMMANDMASK)

# Each transformation becomes an entry in a switch statement
for abbreviation, description in commands.items():
    if isinstance(description,tuple):
        # Transform code exists
        description, source = description
        C_SOURCE+=('   case %s%s: { // %s'%(transform_code_prefix,abbreviation,description))+'\n'
        source = ['      '+l for l in source.split('\n')]
        C_SOURCE+='\n'.join(source)+'\n'
        C_SOURCE+='   } break;\n'
    else:
        # Not implemented yet
        C_SOURCE+=('   case %s%s: // %s'%(transform_code_prefix,abbreviation,description))+'\n'
        C_SOURCE+=('     return NOT_IMPLEMENTED;')+'\n'
        raise ValueError('!!ERROR (prepare_unicode_mapping): Transformation '
            'code %s (%s) is not defined (add this to %s to use it)'%\
            (description,abbreviation,transform_commands_filename))

# End of transformation function
C_SOURCE+=('''\
    default:
      return NOT_IMPLEMENTED;
  }
  return LOADED;
}\n''')

# Print packed data for each block
defined_blocks = []
for codename,(name,start,stop,nassigned) in blockinfo.items():
    C_SOURCE+=('\n'+'/'*80)+'\n'
    C_SOURCE+=('// packed data for 0x%08X-0x%08X "%s"'%(start,stop,name))+'\n'
    tablename = codename+'_map'
    mapdata = 'static const unsigned int %s[] PROGMEM = {\n  '%tablename
    
    # Get the names for the base glyphs for all codepoints in this block
    base_names = []
    transformation_commands = []
    for i in range(start,stop+1):
        # Get character and map to canonical alias, if any
        c = chr(i)
        c = aliasmap.get(c,c)[0]
        
        # Determine the base character, if it ASCII or a direct alias
        # of one of the base glyphs
        # ASCII characters are just the corresponding character literal
        # Unicode characters need to be mapped to their abbreviation
        base_name = None
        if   c in ASCII: base_name = "'\\''" if c=="'" else "'%s'"%c
        elif c in abbreviation_map: base_name = abbreviation_map[c]
        
        # Check if this is a transformed character
        transform = '0'
        if c in decompose and len(decompose[c])>1:
            q = decompose[c][0]
            command = decompose[c][1:]
            if command in commands:
                transform = 'T_'+command
                # Check that this character isn't already defined
                if not base_name is None:
                    raise ValueError(
                        ('%s exists both as a base-glyph and transformed glyph.\n'%c)+
                        ('The offending transform is %s:%s\n'%(c,decompose[c]))+
                        ('Check %s, is %s aliased to a glyph that should be distinct?\n'\
                         %(glyph_aliases_filename,c))
                    )
                # Check that base characer exists
                if   q in ASCII: base_name = "'\\''" if q=="'" else "'%s'"%q
                elif q in abbreviation_map: base_name = abbreviation_map[q]
                if base_name is None:
                    C_SOURCE+=(('// !!!! WARNING '
                        '%s defined as transform %s of %s, '
                        ' but %s is not available as a base glyph')
                          %(c,transform,q,q))+'\n'
                
        # ensure that 0 maps to the replcaement character '�' with no
        # transformation
        if base_name is None: 
            base_name = "0" 
            transform = "0" 
        base_names.append(base_name)
        transformation_commands.append(transform)
    
    # Figure out how much of the block is actually mapped
    # (only store the range of code points for which a mapping exists)
    first_supported_index = -1
    last_supported_index  = -1
    for i,b in enumerate(base_names):
        if b!="0":
            last_supported_index = i
            if first_supported_index<0: first_supported_index = i
    if first_supported_index<0 or last_supported_index<0:
        C_SOURCE+=(
            '// (no code points are mapped in this block)\n'
            'int _%s(unsigned int c) { return NOT_IMPLEMENTED; }\n')%codename
        continue
    C_SOURCE+=('// Offsets %d through %d are mapped in this block'%\
          (first_supported_index,last_supported_index))+'\n'
          
    # Check how sparse the block is
    nsupported = last_supported_index - first_supported_index + 1
    blocklen = stop-start+1
    
    # Prepare glyph map for this block
    # Skip ranges at start/end that are not mapped
    j = 0;
    for i in range(0,stop-start+1):
        if not (i>=first_supported_index and i<=last_supported_index):
            continue
        base_name = base_names[i]
        transform = transformation_commands[i]
        mapdata += (base_name+'|'+transform+',').ljust(14)
        if j%8==7: mapdata+='\n  '
        j+=1
    mapdata+='};'
    C_SOURCE+=(mapdata)+'\n'
    
    # Prepare C subroutine for this unicode block
    C_SOURCE+='//'+'_'*78+'\n'
    C_SOURCE+='// 0x%08X-0x%08X: %s'%(start,stop,name)+'\n'
    # _geometricshapes is an ugly special case
    if codename=='geometricshapes':
        C_SOURCE+=("""int _geometricshapes(unsigned int c) {
          if (c>94) return NOT_IMPLEMENTED;
          unsigned int index = c;
          // Special case: Some parts of geometric shapes stores elsewhere
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
          unsigned int code  = pgm_read_word(geometricshapes_map+index);
          return handle_transform(code);
        }
        """)
    else:
        C_SOURCE+=(
        "int _%s(unsigned int c) {\n"
        "  if (c<%d || c>%d) return NOT_IMPLEMENTED;\n"
        "  unsigned int index = (c-%d);\n"
        "  unsigned int code  = pgm_read_word(%s+index);\n"
        "  return handle_transform(code);\n"
        "}\n"%(codename,first_supported_index,last_supported_index,
             first_supported_index,tablename))
    defined_blocks.append((codename,name,start,stop))

# Write header file
C_SOURCE+=('\n\n#endif // %s\n'%headername)
with open(unicode_mapping_filename,'wb') as f:
    f.write(C_SOURCE.encode('utf8'))
    f.flush()
    f.close()


