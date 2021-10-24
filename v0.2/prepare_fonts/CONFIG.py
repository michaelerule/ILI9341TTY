#!/usr/bin/env python3
"""
Configuration for the font preparation scripts
"""
import os
from pylab import * 
import unicodedata

# Sketch directory into which to place the generated source code
sketchdir = '../Uno9341TTYv16/'

# Names for automatically generated .c and.h files
main_font_filename          = sketchdir+os.sep+'myfont.h'
unicode_mapping_filename    = sketchdir+os.sep+'fontmap.h'
glyphcodes_filename         = sketchdir+os.sep+'glyphcodes.h'
terminal_constants_filename = sketchdir+os.sep+'terminal_constants.h'
diacritics_filename         = sketchdir+os.sep+'combining_diacritics.h'
unicode_blocks_filename     = sketchdir+os.sep+'unicode_blocks.h'

# The main font: image with its bitmaps, textfile with corresponding unicode characters
main_glyph_image_filename = './bitmaps/glyphs.png'
main_glyph_unicode_points = './fontdescription/glyph_codepoints.txt'

# Bitmaps used by the box-drawing code
boxdrawing_image_filename = './bitmaps/boxdrawing.png'

# This should be a python file which defines a variable `commands`, which is
# a dictionary mapping SHORT_NAME → (long name, C source code)
# for all defined transformation
transform_commands_filename = './fontdescription/glyph_transformation_commands.py'

# This should be a python file which defines a variable `decompose`, which is
# a dictionary mapping unicode character → base glyph + transformation code
character_decompositions_filename = './fontdescription/character_decompositions.py'

# Each line of this utf8-encoded text file should contain a collection
# of code-points which should be treated as graphically identically in the font.
glyph_aliases_filename = './fontdescription/aliases.txt'

# Put information about the codepoint ranges for unicode blocks here
# This expects a tab-delimited table with the following columns:
# [Plane][Block range][Block name][Code points][Assigned characters][Scripts]
# This is pulled from https://en.wikipedia.org/wiki/Unicode_block
unicode_block_information_file = './fontdescription/unicode_blocks.txt'

# This defines the bitmap information for combining modifiers. It also
# describes whether the modifiers go above, below, or somewhere else. 
# It also specifies the padding between the character and the modifier.
combining_modifiers_file = './fontdescription/combining_modifiers_bitmaps.txt'

# In case we're not being loaded from the prepare_fonts directory..
import os
here                              = os.path.dirname(__file__) + os.sep
sketchdir                         = os.path.abspath(here + sketchdir)
main_font_filename                = os.path.abspath(here + main_font_filename)
unicode_mapping_filename          = os.path.abspath(here + unicode_mapping_filename)
glyphcodes_filename               = os.path.abspath(here + glyphcodes_filename)
terminal_constants_filename       = os.path.abspath(here + terminal_constants_filename)
diacritics_filename               = os.path.abspath(here + diacritics_filename)
unicode_blocks_filename           = os.path.abspath(here + unicode_blocks_filename)
main_glyph_image_filename         = os.path.abspath(here + main_glyph_image_filename)
main_glyph_unicode_points         = os.path.abspath(here + main_glyph_unicode_points)
boxdrawing_image_filename         = os.path.abspath(here + boxdrawing_image_filename)
transform_commands_filename       = os.path.abspath(here + transform_commands_filename)
character_decompositions_filename = os.path.abspath(here + character_decompositions_filename)
glyph_aliases_filename            = os.path.abspath(here + glyph_aliases_filename)
unicode_block_information_file    = os.path.abspath(here + unicode_block_information_file)
combining_modifiers_file          = os.path.abspath(here + combining_modifiers_file)

# Width and height of terminal cells for each characters
# This is the FULL width and height; alphanumeric glyphs should
# be slightly smaller to allow for spacing. Semigraphics charactere
# may occupy the full size
# 
# Don't change these! At the moment the code is too specialized (optimized)
# for 6x12 characters. 
# 
CW, CH = 6, 12

# Baseline, midline, topline of characters
BASELINE = 2
MIDLINE  = 5
TOPLINE  = 8

# Shape and layout of LCD screen screen 
SCREENW  = 320
SCREENH  = 240
TERMCOLS = int(floor(SCREENW / CW))
TERMROWS = int(floor(SCREENH / CH))
TERMW    = TERMCOLS*CW
TERMH    = TERMROWS*CH
EXTRAW   = SCREENW-TERMW
EXTRAH   = SCREENH-TERMH
PADLEFT  = EXTRAW//2

# Normal alphabetic characters are stored as base glyph + transformation code,
# Packed in an unsigned 16-bit integer. 
# Number of low-bits to use to store the glyph index 
CHARBITS = 9
assert CHARBITS<=10
# Number of high bits to use to store the transform code
TRANSFORMBITS  = 16-CHARBITS
# Maximum number of base glyphs that can be supported in CHARBITS
MAXNCHAR = 2**CHARBITS
# Maximum number of transformation codes that can be supported in CHARBITS
MAXNMODS = 2**TRANSFORMBITS
# Highest allowed glyph index
MAXCHAR  = MAXNCHAR-1
# Highest allowed transformation code
MAXMOD   = MAXNMODS-1
# Mask to extract glpyh index from packed uint16
CHARMASK = MAXNCHAR-1
# Mask to extra transformation code from packed uint16
COMMANDMASK = (MAXNMODS-1)*MAXNCHAR

# Prefix G_ should prevent collisions with other #defines in the C source
glyph_code_prefix     = 'G_'
transform_code_prefix = 'T_'

# Number of columns that the unicode mapping code expects (equal to number
# of columns in main_glyph_image_filename and main_glyph_unicode_points 
NGLYPHCOLS = 32

################################################################################
# Declare which blocks will be handled as base glyph + transform mappings
# Any blocks you wish to support that are not included here should be provided 
# as custom subroutines.
mapped_blocks = [
'basiclatin',
'latin1supplement',
'latinextendeda',
'latinextendedb',
'spacingmodifierletters',
'greekandcoptic',
'cyrillic',
'latinextendedadditional',
'generalpunctuation',
'superscriptsandsubscripts',
'currencysymbols',
'letterlikesymbols',
'arrows',
'mathematicaloperators',
'miscellaneoustechnical',
'geometricshapes',
'cyrillicsupplement',
'greekextended',
'latinextendedc',
#'cyrillicextendeda',
'lisu',
'latinextendede',
'latinextendedf',
'latinextendedg',
'ipaextensions',
'numberforms',
'miscellaneoussymbols',
'dingbats',
'cyrillicextendedb',
'latinextendedd',
'alphabeticpresentationforms',
'arrows',
'miscellaneoussymbolsandpictographs1',
'miscellaneoussymbolsandpictographs2',
'miscellaneoussymbolsandpictographs3',
'armenian',
'georgian',
'devanagari',
'katakana',
'hiragana',
'supplementalarrowsb',
'miscellaneoussymbolsandarrows',
'katakanaphoneticextensions',
'supplementalarrowsc',
]


################################################################################
# Declare unicode blocks that you plan to support as "soft fonts" through
# your own hand-crafted subroutines. This should not overlap the "mapped blocks"
# defined above
softmapped = [
'blockelements',
'boxdrawing',
'braillepatterns',
'combiningdiacriticalmarks',
#'countingrodnumerals',
'enclosedalphanumerics',
#'enclosedalphanumericsupplement',
#'geometricshapesextended',
'halfwidthandfullwidthforms',
'mathematicalalphanumericsymbols',
#'mayannumerals',
#'miscellaneoussymbolsandarrows',
#'smallformvariants',
#'supplementalarrowsa',
#'supplementalarrowsb',
#'supplementalarrowsc',
'symbolsforlegacycomputing',
#'taixuanjingsymbols',
#'yijinghexagramsymbols'
'geometricshapes',
]


# Tidy up
mapped_blocks = [s.lower().replace(' ','').replace('-','')
    for s in mapped_blocks]
softmapped    = [s.lower().replace(' ','').replace('-','')
    for s in softmapped   ]








