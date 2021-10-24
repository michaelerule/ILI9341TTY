#!/usr/bin/env python3


# Define command abbreviations here
# abbreviation for C source code -> (python name, C source to implement)
# This needs to be a list rather than a dictionary so we can detect
# duplicated keys! 
commands = [
('H5',('HREFLECTMAG','mirror_horizontal(1);')),
('H6',('HREFLECTMIN','mirror_horizontal(0);')),
('VU',('VREFLECTMAG','mirror_vertical_uppercase();')),
('VL',('VREFLECTMIN','mirror_vertical_lowercase();')),
('TU',('TURNMAG','mirror_horizontal(1); mirror_vertical_uppercase();')),
('TL',('TURNMIN','mirror_horizontal(1); mirror_vertical_lowercase();')),
('MDL',('MIDDLE_DOT_LOWER'           ,'char_bitmap[CH/2-2] |= 0b001000;')),
('MDR',('MIDDLE_DOT_RIGHT'           ,'char_bitmap[CH/2-1] |= 0b100000;')),
('MDU',('MIDDLE_DOT_UPPER'           ,'char_bitmap[CH/2-1] |= 0b001000;')),
('AAUL',('ACUTE_ACCENT_LEFT'         ,'char_bitmap[CH-1] = char_bitmap[CH-2] = 0b000001;')),
('GA'  ,('GRAVE_ACCENT'              ,'combine_diacritic(COMBINING_GRAVE_ACCENT);')),
('AA'  ,('ACUTE_ACCENT'              ,'combine_diacritic(COMBINING_ACUTE_ACCENT);')),
('XA'  ,('CIRCUMFLEX_ACCENT'         ,'combine_diacritic(COMBINING_CIRCUMFLEX_ACCENT);')),
('XB'  ,('CIRCUMFLEX_ACCENT_BELOW'   ,'combine_diacritic(COMBINING_CIRCUMFLEX_ACCENT_BELOW);')),
('TA'  ,('TILDE'                     ,'combine_diacritic(COMBINING_TILDE);')),
('MA'  ,('MACRON'                    ,'combine_diacritic(COMBINING_MACRON);')),
('OBA' ,('OVERLINE'                  ,'combine_diacritic(COMBINING_OVERLINE);')),
('BA'  ,('BREVE'                     ,'combine_diacritic(COMBINING_BREVE);')),
('OA'  ,('DOT_ABOVE'                 ,'combine_diacritic(COMBINING_DOT_ABOVE);')),
('DA'  ,('DIAERESIS'                 ,'combine_diacritic(COMBINING_DIAERESIS);')),
('RA'  ,('RING_ABOVE'                ,'combine_diacritic(COMBINING_RING_ABOVE);')),
('DAA' ,('DOUBLE_ACUTE_ACCENT'       ,'combine_diacritic(COMBINING_DOUBLE_ACUTE_ACCENT);')),
('CRA' ,('CARON'                     ,'combine_diacritic(COMBINING_CARON);')),
('VLA' ,('VERTICAL_LINE_ABOVE'       ,'combine_diacritic(COMBINING_VERTICAL_LINE_ABOVE);')),
('DGA' ,('DOUBLE_GRAVE_ACCENT'       ,'combine_diacritic(COMBINING_DOUBLE_GRAVE_ACCENT);')),
('CBU' ,('CANDRABINDU'               ,'combine_diacritic(COMBINING_CANDRABINDU);')),
('IBA' ,('INVERTED_BREVE'            ,'combine_diacritic(COMBINING_INVERTED_BREVE);')),
('CMB' ,('COMMA_BELOW'               ,'combine_diacritic(COMBINING_COMMA_BELOW);')),
('CDL' ,('CEDILLA'                   ,'combine_diacritic(COMBINING_CEDILLA);')),
('FRMT',('FERMATA'                   ,'combine_diacritic(COMBINING_FERMATA);')),
('HKAB',('HOOK_ABOVE'                ,'combine_diacritic(COMBINING_HOOK_ABOVE);')),
('OBLW',('DOT_BELOW'                 ,'combine_diacritic(COMBINING_DOT_BELOW);')),
('LBLW',('LINE_BELOW'                ,'combine_diacritic(COMBINING_LOW_LINE);')),
('TBLW',('TILDE_BELOW'               ,'combine_diacritic(COMBINING_TILDE_BELOW);')),
('BBLW',('BREVE_BELOW'               ,'combine_diacritic(COMBINING_BREVE_BELOW);')),
('DBLW',('DIAERESIS_BELOW'           ,'combine_diacritic(COMBINING_DIAERESIS_BELOW);')),
('RHRA',('RIGHT_HALF_RING_ABOVE'     ,'combine_diacritic(COMBINING_RIGHT_HALF_RING_ABOVE);')),
('GDT' ,('GREEK_DIALYTIKA_TONOS'     ,'combine_diacritic(COMBINING_GREEK_DIALYTIKA_TONOS);')),
('DVLB',('DOUBLE_VERTICAL_LINE_BELOW','combine_diacritic(COMBINING_DOUBLE_VERTICAL_LINE_BELOW);')),
('MBLW',('MACRON_BELOW'              ,'combine_diacritic(COMBINING_MACRON_BELOW);')),
('SVSM',('SEMIVOICED_SOUND_MARK'     ,'combine_diacritic(COMBINING_SEMIVOICED_SOUND_MARK);')),
('VSM' ,('VOICED_SOUND_MARK'         ,'combine_diacritic(COMBINING_VOICED_SOUND_MARK);')),
('LHRA',('LEFT_HALF_RING_ABOVE'      ,'combine_diacritic(COMBINING_LEFT_HALF_RING_ABOVE);')),
('AEM' ,('EMPHASIS_MARK'             ,'combine_diacritic(COMBINING_EMPHASIS_MARK);')),
('AEP' ,('EXCLAMATION_MARK'          ,'combine_diacritic(COMBINING_EXCLAMATION_MARK);')),
('AQM' ,('QUESTION_MARK'             ,'combine_diacritic(COMBINING_QUESTION_MARK);')),
('DICB',('DEVANAGARI_INVERTED_CANDRABINDU','combine_diacritic(COMBINING_DEVANAGARI_SIGN_INVERTED_CANDRABINDU);')),
('DCB' ,('DEVANAGARI_CANDRABINDU'    ,'combine_diacritic(COMBINING_DEVANAGARI_SIGN_CANDRABINDU);')),
('DSAN',('DEVANAGARI_ANUSVARA'       ,'combine_diacritic(COMBINING_DEVANAGARI_SIGN_ANUSVARA);')),
('DSOE',('DEVANAGARI_OE'             ,'combine_diacritic(COMBINING_DEVANAGARI_VOWEL_SIGN_OE);')),
('DSNK',('DEVANAGARI_NUKTA'          ,'combine_diacritic(COMBINING_DEVANAGARI_SIGN_NUKTA);')),
('DVSU',('DEVANAGARI_U'              ,'combine_diacritic(COMBINING_DEVANAGARI_VOWEL_SIGN_U);')),
('DSUU',('DEVANAGARI_UU'             ,'combine_diacritic(COMBINING_DEVANAGARI_VOWEL_SIGN_UU);')),
('DSVR',('DEVANAGARI_VOCALIC_R'      ,'combine_diacritic(COMBINING_DEVANAGARI_VOWEL_SIGN_VOCALIC_R);')),
('DSRR',('DEVANAGARI_VOCALIC_RR'     ,'combine_diacritic(COMBINING_DEVANAGARI_VOWEL_SIGN_VOCALIC_RR);')),
('DSCE',('DEVANAGARI_CANDRA_E'       ,'combine_diacritic(COMBINING_DEVANAGARI_VOWEL_SIGN_CANDRA_E);')),
('DSSR',('DEVANAGARI_SHORT_E'        ,'combine_diacritic(COMBINING_DEVANAGARI_VOWEL_SIGN_SHORT_E);')),
('DSE' ,('DEVANAGARI_E'              ,'combine_diacritic(COMBINING_DEVANAGARI_VOWEL_SIGN_E);')),
('DSAI',('DEVANAGARI_AI'             ,'combine_diacritic(COMBINING_DEVANAGARI_VOWEL_SIGN_AI);')),
('DSUD',('DEVANAGARI_UDATTA'         ,'combine_diacritic(COMBINING_DEVANAGARI_STRESS_SIGN_UDATTA);')),
('DSAU',('DEVANAGARI_ANUDATTA'       ,'combine_diacritic(COMBINING_DEVANAGARI_STRESS_SIGN_ANUDATTA);')),
('DSGA',('DEVANAGARI_GRAVE'          ,'combine_diacritic(COMBINING_DEVANAGARI_GRAVE_ACCENT);')),
('DSAA',('DEVANAGARI_ACUTE'          ,'combine_diacritic(COMBINING_DEVANAGARI_ACUTE_ACCENT);')),
('DCEE',('DEVANAGARI_VOWEL_CANDRA_LONG_E','combine_diacritic(COMBINING_DEVANAGARI_VOWEL_SIGN_CANDRA_LONG_E);')),
('DSUE',('DEVANAGARI_UE'             ,'combine_diacritic(COMBINING_DEVANAGARI_VOWEL_SIGN_UE);')),
('DUUE',('DEVANAGARI_UUE'            ,'combine_diacritic(COMBINING_DEVANAGARI_VOWEL_SIGN_UUE);')),
('DSVL',('DEVANAGARI_VOCALIC_L'      ,'combine_diacritic(COMBINING_DEVANAGARI_VOWEL_SIGN_VOCALIC_L);')),
('DSLL',('DEVANAGARI_VOCALIC_LL'     ,'combine_diacritic(COMBINING_DEVANAGARI_VOWEL_SIGN_VOCALIC_LL);')),
('CDAL',('CEDILLA_ABOVE_LOWER',
       'char_bitmap[MIDLINE+4] |= 0b011000;'
       'char_bitmap[MIDLINE+3] |= 0b001000;')),
('DSU',('DIAGONAL_STROKE_UPPER',
       'char_bitmap[BASELINE+6] |= 0b100000;\n'
       'char_bitmap[BASELINE+5] |= 0b010000;\n'
       'char_bitmap[BASELINE+4] |= 0b010000;\n'
       'char_bitmap[BASELINE+3] |= 0b001000;\n'
       'char_bitmap[BASELINE+2] |= 0b000100;\n'
       'char_bitmap[BASELINE+1] |= 0b000100;\n'
       'char_bitmap[BASELINE+0] |= 0b000010;')),
('DSL',('DIAGONAL_STROKE_LOWER',
       'char_bitmap[BASELINE+4] |= 0b100000;\n'
       'char_bitmap[BASELINE+3] |= 0b010000;\n'
       'char_bitmap[BASELINE+2] |= 0b001000;\n'
       'char_bitmap[BASELINE+1] |= 0b000100;\n'
       'char_bitmap[BASELINE+0] |= 0b000010;')),
('ONR',('OGONEK_RIGHT',
       'char_bitmap[BASELINE-1] |= 0b010000;'
       'char_bitmap[BASELINE-2] |= 0b110000;')),
('ONM',('OGONEK_MIDDLE',
       'char_bitmap[BASELINE-1] |= 0b001000;'
       'char_bitmap[BASELINE-2] |= 0b011000;')),
('RAV',('CARON_VARIANT',
       'if ((char_bitmap[9]&0b100000)||(char_bitmap[8]&0b100000)) {\n'
       '  for (byte i=0; i<CH; i++) {\n'
       '    char_bitmap[i] = (char_bitmap[i]|((char_bitmap[i]&0b100000)>>1))&0b011111;\n'
       '  }\n'
       '}\n'
       'char_bitmap[9] |= 0b100000;\n'
       'char_bitmap[8]  |= 0b100000;')),
('HK1',('LOWER_RIGHT_TAIL',
       'char_bitmap[BASELINE-1] |= 0b100000;'
       'char_bitmap[BASELINE-2] |= 0b010000;')),
('HK2',('HOOK_2',
       'char_bitmap[BASELINE-1] |= 0b100000;'
       'char_bitmap[BASELINE-2] |= 0b110000;')),
('HK3',('PALATAL_HOOK',
       'char_bitmap[BASELINE-1] |= 0b100000;'
       'char_bitmap[BASELINE-2] |= 0b011000;')),
('AALL',('APOSTROPHE_ABOVE_LEFT_LOWER',
       'char_bitmap[MIDLINE+4] |= 0b000001;'
       'char_bitmap[MIDLINE+3] |= 0b000001;')),
('SMLFH',('STROKE_MID_LEFT_HALF',
       'char_bitmap[5] |= 0b000111;')),
('SUMLH',('STROKE_UPPER_MID_RIGHT_HALF',
       'char_bitmap[8] |= 0b111000;')),
('SUF',('STROKE_UPPER_FULL',
       'char_bitmap[7] |= 0b111111;')),
('SMF',('STROKE_MIDDLE_FULL',
       'char_bitmap[6] |= 0b011111;')),
('SULH',('STROKE_UPPER_LEFT_HALF',
       'char_bitmap[8] |= 0b000111;')),
('LDS',('DIAGONAL_STROKE_LEFT',
       'char_bitmap[4] |= 0b000110;'
       'char_bitmap[5] |= 0b000011;')),
('DSM',('DIAGONAL_STROKE_MID',
       'char_bitmap[5] |= 0b011000;'
       'char_bitmap[6] |= 0b001100;')),
('SMMH',('STROKE_MID_MID_HALF',
       'char_bitmap[5] |= 0b011100;')),
('SMLH',('STROKE_MID_LOWER_HALF',
       'char_bitmap[4] |= 0b011110;')),
('DS1',('RIGHT_DESCENDER',
       'char_bitmap[1] |= 0b100000;'
       'char_bitmap[0] |= 0b100000;')),
('MRD',('MIDRIGHT_DESCENDER',
       'char_bitmap[1] |= 0b010000;'
       'char_bitmap[0] |= 0b010000;')),
('KDS',('KDIAGONAL_STROKE',
       'char_bitmap[4] |= 0b100000;\n'
       'char_bitmap[3] |= 0b010000;\n'
       'char_bitmap[2] |= 0b001000;')),
('LDSC',('LEFT_DESCENDER',
       'char_bitmap[1] |= 0b000010;\n'
       'char_bitmap[0] |= 0b000010;')),
('LVT',('LVERTTICK',
       'char_bitmap[7] |= 0b000001;')),
('LHU',('LEFT_HOOK_UPPER',
       'for (byte i=0; i<CH; i++) char_bitmap[i] = (0b111100&char_bitmap[i]) | ((char_bitmap[i]&0b000011)<<1);\n'
       'char_bitmap[8] |= 0b000011;\n'
       'char_bitmap[7] |= 0b000001;')),
('RHU',('RIGHT_HOOK_UPPER',
       'for (byte i=0; i<CH; i++) char_bitmap[i] = (0b001111&char_bitmap[i]) | ((char_bitmap[i]&0b110000)>>1);\n'
       'char_bitmap[8] |= 0b110000;\n'
       'char_bitmap[7] |= 0b100000;')),
('BLD',('BOLD','hboldright();')),
('VBD',('VERYBOLD','hboldright(); hboldleft();')),
('TMB',('ENTOMB','entomb();')),
('ITA',('ITALIC','italicize();')),
('BLDIT',('BOLDITALIC','bold; italicize();')),
('OLN',('OUTLINE','outline();')),
]





