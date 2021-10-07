#!/usr/bin/env bash
# sudo apt-get install xcftools to get xcf2png

# Run all font preparation scripts

echo "Converting xcf to png files..."
cd ./bitmaps
./allxcf2png
cd ../

echo "Preparing basic terminal information..."
/usr/bin/env python3 prepare_terminal_constants.py

echo "Preparing packed data for the main font glyphs and box drawing..."
/usr/bin/env python3 prepare_main_font_bitmaps.py

echo "Preparing mapping information for unicode..."
/usr/bin/env python3 prepare_unicode_mapping.py

echo "Preparing combining diacritics code..."
/usr/bin/env python3 prepare_combining_diacritics.py

echo "Preparing header to delcare which unicode blocks are supported..."
/usr/bin/env python3 prepare_unicode_header.py

echo "(DONE)"


