

Contents:

- `prepare_all.sh`: Run me to prepare everything
- `CONFIG.py`: Tell the computer what you've named everything, where to find it, etc. 
- `prepare_terminal_constants.py`: Generate header for constants for the terminal
- `prepare_main_font_bitmaps.py`: Generate header for font bitmaps
- `prepare_combining_diacritics.py`: Generate header for combining diacritics
- `prepare_unicode_mapping.py`: Generate header for mapped unicode points
- `font_utilities.py`: This script contains subroutines.
- `bitmaps`: This folder contains font bitmaps
- `fontdescription`: This folder contains information needed to define the font


Requires:

- An Ubuntu-like Linux environment
- `Python3`
- Common Python modules: `numpy`, `matplotlib`, `pylab`
- Other Python modules (install via pip3): `unicodedata`
- `Gimp` (if you want to automatically convert `.xcf` to `.png`)

In `fontdescription`:

- `aliases.txt`: Each line of this file is a collection of unicode characters that should be treated as graphically identical in our font. 
- `character_decompositions.py`: This table describes how to construct composed characters in terms of a base-glyph and a transformation or combining modifier.
- `combining_modifiers_bitmaps.txt`: This file defines combining diacritics (bitmaps, location, names, spacing).
- `glyph_codepoints.txt`: This file specifies the unicode characters for the glyphs drawn in `glyphs.xcf`.
- `glyph_transformation_commands.py`: This file specifies combining modifiers and other transformations.
- `glyph_transformation_subroutines.c`: This file contains some C subroutines for transformations.
- `unicode_blocks.txt`: This file contains a table of information about unicode blocks.


In `bitmaps`:

- `glyphs.xcf`: Image defining the bitmap font. 512 characters. 
- `boxdrawing.xcf`: Image defining some semigraphics characters we need. 
- `legacycomputingcharacters.xcf`: Not currentl used
- `modifiers.xcf`: Not currently used
- `xcf2png_replacement.sh`: Script to call Gimp to convert `.xcf` to `.png`
- `allxcf2png`: Script to convert all `.xcf` to `.png`
