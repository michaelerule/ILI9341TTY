#!/usr/bin/env python3
"""
Prepare the header file which defines which unicode ranges are supported
"""

from CONFIG         import *
from font_utilities import *

# Tidy up
mapped_blocks = [s.lower().replace(' ','').replace('-','')
    for s in mapped_blocks]
softmapped    = [s.lower().replace(' ','').replace('-','')
    for s in softmapped   ]

# Check that there is no overlaps
if 'basiclatin' in mapped_blocks:
    raise ValueError('!! basiclatin is supported by default and should not'
        ' be included in the mapped unicode blocks')
if 'basiclatin' in softmapped:
    raise ValueError('!! basiclatin is supported by default and should not'
        ' be included in the software mapped blocks')
overlap = set(mapped_blocks) & set(softmapped)
if len(overlap):
    raise ValueError('!! The following blocks are defined as both mapped and software-mapped:'+\
        ' '.join(overlap))
        
################################################################################
# Start of source code
C_SOURCE   = ''
headername = unicode_blocks_filename.split('/')[-1].split('.')[0].upper()
C_SOURCE += "#ifndef %s_H\n"%headername
C_SOURCE += "#define %s_H\n"%headername
C_SOURCE += '// This file is automatically generated, do not edit it,\n'
C_SOURCE += '// see ./prepare_fonts/README.md for more information. \n'
C_SOURCE += '\n'

################################################################################
# Declare handling routine for each block
# Also determine starting/ending ranges for each block
C_SOURCE += '// The following unicode blocks are supported:\n'
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
    C_SOURCE += ('int _%s(uint16_t c); // 0x%08X-0x%08X\n'%(shortname,start,stop))
    starts.append(start//16)
    lengths.append(length//16)
    fn_names.append('_'+shortname)
starts  = array(starts)
lengths = array(lengths)

def pack80(name,data):
    global C_SOURCE
    bits = int(ceil(ceil(log2(max(data)))/8))*8
    lenvar = 'N_'+name.replace(' ','_').upper()
    l = len(data)
    line = 'static const uint%d_t %s[] PROGMEM = {'%(bits,name)
    for i in data:
        s = '0x%X,'%i
        if len(line)+len(s)>180:
            C_SOURCE += (line)+'\n'
            line = '  '
        line += s
    C_SOURCE += line + '};\n\n'

C_SOURCE += '\n'
C_SOURCE += ('// Number of blocks defined')+'\n'
C_SOURCE += ('#define NBLOCKS (%d)'%len(lengths))+'\n'+'\n'
C_SOURCE += ('// Starting unicode point of each defined block, divided by 16')+'\n'
pack80('block_starts_x16',starts)
C_SOURCE += ('// Number of codepoints in each block, divided by 16')+'\n'
pack80('block_lengths_x16',lengths)
C_SOURCE += ('// Function pointers to subroutines to handle each block')+'\n'
s = 'static int(*const unicode_block[])(uint16_t) = {'
for n in fn_names:
    q = n+','
    if len(s+q)>180:
        C_SOURCE += (s)
        s = '  '
    s += q
C_SOURCE += '\n'
C_SOURCE += (s+'};')+'\n'+'\n'
C_SOURCE += ('// Last supported row in unicode tables')+'\n'
C_SOURCE += ('#define LASTROW (0x%X)'%((starts+lengths)[-1]-1))+'\n'

C_SOURCE += '\n'
C_SOURCE += "#endif /*%s_H*/\n"%headername
with open(unicode_blocks_filename,'wb') as f:
    f.write(C_SOURCE.encode('utf8'))
    f.flush()
    f.close()











