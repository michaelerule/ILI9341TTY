#!/usr/bin/env python3
"""
Routines for preparing font information for C source code
"""
from matplotlib.image import imread
import numpy as np
from pylab import *
import unicodedata
from CONFIG import *

################################################################################
# Useful constants
ASCII = (" !\"#$%&\'()*+,-./0123456789:;<=>?@"
         "ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`"
         "abcdefghijklmnopqrstuvwxyz{|}~")

################################################################################
# Execfile is sensible for organizing configuration information into 
# separate files, but keeping everything in a common namespace
#https://stackoverflow.com/a/41658338/900749
def execfile(filepath, globals=None, locals=None):
    if globals is None: 
        globals = {}
    globals.update({
        "__file__": filepath,
        "__name__": "__main__",
    })
    with open(filepath, 'rb') as file:
        exec(compile(file.read(), filepath, 'exec'), globals, locals)

################################################################################
def get_unicode_blocks_information():
    '''
    Load information on unicode blocks (pulled from Wikipedia)
    
    Returns
    -------
    blockinfo: dictionary, block name -> (name,start,stop,# assigned)
    '''
    blockinfo = {}
    with open(unicode_block_information_file,'r') as f:
        blocks = f.readlines()
        for ib,l in enumerate(blocks):
            _,blockrange,name,ncodepoints,nassigned,scripts = l.split('\t')
            codename = name.lower().replace(' ','').replace('-','')
            start, stop = [int(i[2:],16) for i in blockrange.split('..')]
            length    = int(ncodepoints.replace(',',''))
            nassigned = int(nassigned.replace(',',''))
            blockinfo[codename]=(name,start,stop,nassigned)
        return blockinfo
    assert False

################################################################################
def pack_bits(character,
    mirror_vertical   = True ,
    mirror_horizontal = False,
    pack_sideways     = False,
    reverse_bits      = False):
    '''
    Pack a black-and-white (binary) character bitmap into a bit vector. 
    
    Parameters
    ----------
    characters: charrows x charcolumns character bitmap as binary {0,1} 2D numpy array
    mirror_vertical: if True, ⇒ font data starts at base of character, upwards
    mirror_horizontal: if False, ⇒ Leftmost column goes in lowest-order bit
    pack_sideways: if False, ⇒ Bits are packed in row-major order
    reverse_bits: if False, ⇒ Do not reverse the bit order within each byte
    
    Returns
    -------
    bytes: packed bytes for this character
    '''
    if mirror_vertical  : character=character[::-1,:];
    if mirror_horizontal: character=character[:,::-1];
    if pack_sideways    : character=character.T;
    bits = 2**arange(8)
    if reverse_bits: bits = bits[::-1]
    NBITS  = prod(shape(character))
    BYTESPERCHAR = int(ceil(NBITS/8))
    q = zeros(BYTESPERCHAR*8)
    q[:NBITS] = character.ravel()
    return q.reshape(BYTESPERCHAR,8)@bits

################################################################################
def pack_font(imagefilename, CW, CH, 
                PADLEFT  = 0, 
                PADABOVE = 0, 
                fontname = None,
                mirror_vertical  = True ,
                mirror_horizontal= False,
                pack_sideways    = False,
                reverse_bits     = False):
    '''
    Convert a font bitmap in a PNG image file. 
    
    Parameters
    ----------
    imagefilename: string containing path to image
    CW: horizontal spacing of characters in image, in pixels
    CH: vertical spacing of characters in image, in pixels
    PADLEFT: number of columns of padding to the left of each character (this will be stripped)
    PADABOVE: number of columns of padding above each character (this will be stripped)
    fontname: Optional name to use for packed font variables in sourcecode; Defaults to `imagefilename` if None
    mirror_vertical: if True, ⇒ font data starts at base of character, upwards
    mirror_horizontal: if False, ⇒ Leftmost column goes in lowest-order bit
    pack_sideways: if False, ⇒ Bits are packed in row-major order
    reverse_bits: if False, ⇒ Do not reverse the bit order within each byte
    
    Returns
    -------
    string: C source code for bit-packed character data
    '''
    if CW>8:
        raise ValueError('Characters wider than 8 pixels not supported')
    assert PADLEFT<CW
    assert PADABOVE<CH
    
    if fontname==None:
        fontname = imagefilename.split('/')[-1]
        fontname = fontname.split('.')[0].lower()
    
    img = imread(imagefilename)
    
    pixelstall, pixelswide, color_channels = img.shape
    
    if not (pixelstall%CH==0):
        raise ValueError('Image height %d cannot be divided equally into units of %d pixels'%(pixelstall,CH))
    if not (pixelswide%CW==0):
        raise ValueError('Image width %d cannot be divided equally into units of %d pixels'%(pixelswide,CW))
    
    # Ignore alpha or any extra channels if present
    if color_channels>3: 
        img = img[:,:,:3]
    
    NCOLS  = pixelswide // CW
    NROWS  = pixelstall // CH
    NCHARS = NCOLS*NROWS
    print('Detected %d columns'%NCOLS)
    print('Detected %d rows'%NROWS)

    # Grab bit values by checking for white pixels
    x = np.all(img==1.0,axis=2)[:CH*NROWS,:CW*NCOLS]
    figure(imagefilename)
    imshow(x,interpolation='nearest'); 
    subplots_adjust(0,0,1,1,0,0);
    axis('off')
    
    # Re-order into a list of HxW characters
    u=x.reshape(NROWS,CH,NCOLS,CW).transpose(0,2,1,3).reshape(NCHARS,CH,CW)
    
    # Strip padding
    u = u[:,PADABOVE:,PADLEFT:]

    NBITS  = (CW-PADLEFT)*(CH-PADABOVE)
    BYTESPERCHAR = int(ceil(NBITS/8))
    NBYTES = NCHARS*BYTESPERCHAR

    # Ensure name is a safe C identifier
    fontname = fontname.upper();
    allowed  = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ01234567890'
    fontname = ''.join([c if c in allowed else '_' for c in fontname])
    while '__' in fontname: fontname = fontname.replace('__','_')
    while len(fontname) and fontname[0] in '1234567890': fontname = fontname[1:]
    if len(fontname)<2: 
        raise ValueError('Unable to generate a valid C variable name from file name',imagefilename)
    print('Font name for C source code is "%s"'%fontname)
    
    # Define information for this font/glyph data
    C_SOURCE = ''
    C_SOURCE += '#define BYTESPERCHAR_%s (%d)\n'%(fontname,BYTESPERCHAR)
    C_SOURCE += '#define NBYTES_%s       (%d)\n'%(fontname,NBYTES)
    C_SOURCE += '#define CHAR_W_PX_%s    (%d)\n'%(fontname,CW-PADLEFT)
    C_SOURCE += '#define CHAR_H_PX_%s    (%d)\n'%(fontname,CH-PADABOVE)  
    C_SOURCE += '#define NCHARS_%s       (%d)\n'%(fontname,NCHARS)    
    
    # Print array data source code
    C_SOURCE += 'static const uint8_t font_%dx%d_%s[NBYTES_%s] PROGMEM = {'\
    %(CW,CH,fontname.lower(),fontname)
    textwidth = 80
    text = []
    line = '\n  '
    charbytes = concatenate([pack_bits(ui,
                mirror_vertical  ,
                mirror_horizontal,
                pack_sideways    ,
                reverse_bits     ) for ui in u])
    for i in charbytes.ravel():
        if len(line+','+str(i))>textwidth:
            text.append(line)
            line = ''
        line += '%d'%i+','
    text += [line]
    C_SOURCE += '\n  '.join(text)
    C_SOURCE += '};\n'
    
    # Provide a hint for how to unpack the font data
    if  mirror_vertical  == True  and\
        mirror_horizontal== False and\
        pack_sideways    == False and\
        reverse_bits     == False:
        # We have some source code to handle this case
        C_SOURCE += '\n// Use this to unpack font data form %s into a %dx%d character\n'%(fontname,CH,CW)
        C_SOURCE += '// Assuming a length-%d global array char_bitmap exists\n'%(CH)
        C_SOURCE += '/*\n'
        nr = CH-PADABOVE
        nc = CW-PADLEFT
        i_in  = 0
        i_out = 0
        bits_remaining = 8
        zeropad = '0'*PADLEFT
        for i_out in range(nr):
            C_SOURCE += 'char_bitmap[%2d]='%i_out
            if bits_remaining>=nc:
                if 8-bits_remaining-1<0:
                    C_SOURCE += ' (charbytes[%d]<<%d) & 0b'%(i_in,-(8-bits_remaining-PADLEFT)) +\
                        '1'*nc + zeropad + ';\n'
                else:
                    C_SOURCE += ' (charbytes[%d]>>%d) & 0b'%(i_in,8-bits_remaining-PADLEFT) + \
                        '1'*nc + zeropad + ';\n'
                bits_remaining-=nc
            else:
                C_SOURCE += '((charbytes[%d]>>%d) & 0b'%\
                    (i_in,8-bits_remaining-PADLEFT) + ('1'*bits_remaining+zeropad).ljust(5) + ')'
                i_in += 1
                C_SOURCE += ' | ((charbytes[%d] & 0b%s) << %d' %\
                    (i_in, ('1' * (nc - bits_remaining) ).ljust(4), bits_remaining+PADLEFT) + ');\n'
                bits_remaining = 8-(nc-bits_remaining)
            if bits_remaining==0:
                bits_remaining = 8
                i_in += 1
        i_out+=1
        while i_out<CH:
            C_SOURCE += ('char_bitmap[%2d] = 0;'%(i_out))+'\n'
            i_out += 1
        C_SOURCE += '*/'
    else:
        C_SOURCE += '// Note: automatic unpacking code not yet implemented for\n'
        C_SOURCE += '// mirror_vertical == %s\n'%mirror_vertical
        C_SOURCE += '// mirror_horizontal == %s\n'%mirror_horizontal
        C_SOURCE += '// pack_sideways == %s\n'%pack_sideways
        C_SOURCE += '// reverse_bits == %s\n'%reverse_bits
    return C_SOURCE
    
################################################################################
def rebuild_aliasmap(aliases,codepoints):
    '''
    Clean up the aliases defined in aliases.text and check that they work
    with the current font definitions. 
    - Confirm that distinct glyphs are not set as aliases
    - Confirm that each unicode character appears in at most one alias set
    
    Parameters
    ----------
    aliases: list of alias sets
    codepoints: iterable of characters available as glyphs in this font
    
    Returns
    -------
    aliasmap: a mapping from unicode characters to their alias sets
    '''
    aliases  = [sorted(list(set(a))) for a in aliases]
    aliasmap = {}
    for a in aliases:
        # Ensure we don't merge separate glyphs
        intersect = set(codepoints)&set(a)
        if len(intersect)>1:
            raise ValueError('Glyphs aliased, but distinct in font: %s'%intersect)
        # Make sure aliases are unique
        for c in a:
            if c in aliasmap:
                raise ValueError('Aliases already defined for %s: %s'%(c,aliasmap[c]))
            aliasmap[c]=''.join(sorted(list(set(a))))#[0]
    return aliasmap


def generate_codepoint_name_abbreviation(c, aliases, abbreviation_map):
    '''
    Generates an abbreviated name for a given unicode point.
    ASCII characters are simply abbreviated by the corresponding character literal. 
    For other characters, the unicode name is heuristically abbreviated to
    a 2-5 character literal that can be used to refer to it in the C 
    source code
    
    Parameters
    ----------
    c: unicode character to abbreviate
    aliases: a list of alias sets for characters that should be graphically identical
    abbreviation_map: iterable of abbreviations that are already defined (so we can avoid collisions)
    
    Returns
    -------
    shortname: abbreviation to use in C source code
    name: a string summarizing all unicode aliases mapped to this glyph
    
    Modifies
    --------
    This will add the abbreviation to the argument `abbreviation_map` if one
    is successfully created.
    '''

    if c in ASCII:
        return (None, None)
    name = unicodedata.name(c).lower()
    
    # For digits, it's clearer to use the actual numbers in variable names
    for i,n in enumerate('zero one two three four five six seven eight nine'.split()):
        name = name.replace(' '+n,' %d'%i)
        
    # Ignore language when designing abbreviated name
    s = name.split()
    for l in 'latin greek cyrillic'.split():
        if s[0]==l: s=s[1:]
        
    # Try to create abbreviation, appending "collision_resolver" if two names are the same
    found_name=False;
    for collision_resolver in ['']+list('23456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                                        'abcdefghijklmnopqrstuvwxyz01'):
        shortname = ''
        
        # Letters and ligatures are named by their descriptions
        if 'letter' in s:
            q = s[s.index('letter')+1:]
            if len(q)>1: shortname += ''.join([qi[0] for qi in q]).upper()
            else:        shortname += q[0].upper()[:4]
        if 'ligature' in s:
            q = s[s.index('ligature')+1:]
            if len(q)>1: shortname += ''.join([qi[0] for qi in q]).upper()
            else:        shortname += q[0].upper()[:4]
            
        # Other characters... we just grab whatever is in the unicode name
        if len(shortname)==0:
            if len(s)>1:
                end = ''.join([si[0] for si in s[1:]])
                clip = max(1,min(4,len(s[0]))-len(end))
                shortname = (s[0][:clip]+end).upper()[:4]
            else:
                shortname = ''.join(s).upper()[:4]
                
        # For common modifications we add a suffix
        if any([q in s for q in 'small capital symbol'.split()]):
            shortname = shortname[:3]
        if len(collision_resolver)>0:
            shortname = shortname[:-1]+collision_resolver
        if 'small'   in s: shortname += 'L'
        if 'capital' in s: shortname += 'U'
        if 'symbol'  in s: shortname += 'M'
        
        # Add prefix and check for collisions
        shortname = glyph_code_prefix + shortname
        if not shortname in abbreviation_map.values():
            abbreviation_map[c]=shortname
            found_name = True
            break

    # Note which aliases map to this code point
    if c in aliases:
        omit = set(name.lower().split())
        name += ' +'.join([
            ' '.join([
            s for s in unicodedata.name(a).lower().split() 
            if not s in omit]) 
            for a in aliases[c]
        ])
    
    return shortname, name
