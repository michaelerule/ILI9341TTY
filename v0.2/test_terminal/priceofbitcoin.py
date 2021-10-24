#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Practical aplications of retro-arduino-tty unclear. 
Practical aplications of bitcoin unclear. 
Demonstrate retro-arduino-tty by plotting recent price of bitcoin.
'''

import os
import sys
import requests
import numpy  as np
import pandas as pd
from numpy import *
from sty   import *

################################################################################
# Constants

MAXROWS = 24
api_url = "https://api.kraken.com"

interval = 240

RATE_LIMIT_DELAY_SECONDS = 0

# Get terminal size; Adjust plot height to fit if needed
columns, rows = os.get_terminal_size(0)
NROWS = min(MAXROWS, rows-4)

################################################################################
# Terminal colors 

# Some nice colors
BLACK      = 0
RUST       = 209
OCHRE      = 214
AZURE      = 75
TURQUOISE  = 45
MAUVE      = 176
DARKMAUVE  = 90
MOSS       = 114
LITEGREEN  = 119
DARKGREEN  = 22
DARKGRAY   = 235
GRAY       = 240
OLIVE      = 58
BROWN      = 100

# Colors for startup logo (medium green)
logocolor = bg.rs + fg(LITEGREEN)

# Background and foreground colors for logging messages
logbg     = bg(DARKMAUVE)
logcolor1 = fg(RUST)
logcolor2 = fg(OCHRE)
prefix    = 'log'

# Fill colors for background, low-high range, and below the low price
bgcolor    = bg.rs     # black (background of plot
linecolor  = MAUVE     # shade between high, low price
fill_color = DARKMAUVE # shade blow line in plot

# Colors of major/minor lines above/below plot
minor_line_color        = fg(DARKGRAY)
major_line_color        = fg(GRAY)
minor_line_color_filled = fg(OLIVE) 
major_line_color_filled = fg(BROWN)

# Color of x and y axis labels
labelcolor = bg.rs + fg(OCHRE)

# Terminal control codes
CONTROL            = '\x1b'
CSI                = CONTROL+'['
clearafter         = CSI + '0J'
clearbefore        = CSI + '1J'
clearscreen        = CSI + '2J'
clearscreen2       = CSI + '3J'
clearright         = CSI + '0K'
clearleft          = CSI + '1K'
clearline          = CSI + '2K'
underline          = CSI + '3m'
underline          = CSI + '4m'
double_underline_1 = CSI + '21m'
double_underline_2 = CSI + '61m'
overline_1         = CSI + '53m'
overline_2         = CSI + '62m'
double_overline    = CSI + '63m'
strike             = CSI + '9m'
verybold           = CSI + '20m'
vtab               = '\x0b'
upstart            = CSI+'F'
downstart          = CSI+'E'
savecursor         = '\x1b7'
restorecursor      = '\x1b8'
showcursor         = CSI+"?25h"
hidecursor         = CSI+"?25l"
reset              = '\x1bc'
getcursor          = CSI+'6n'

print(reset+hidecursor,flush=True,end='')

################################################################################
# Formatted status messages

def LOG(msg,newline=False):
    sys.stdout.write('\r'
         + logbg + logcolor1 + (prefix+': ').rjust(6)    + rs.all
         + logbg + logcolor2 + str(msg).ljust(columns-6) + rs.all
         + ('\n' if newline else ''))
    sys.stdout.flush()

def unpack_json(response):
    if response['error']:
        raise ValueError('Server returned error code:'+str(response['error']))
    return response['result']

def public_call(command, **kwargs):
    try:
        resp = requests.post(api_url+'/0/public/'+command, data=kwargs)
    except:
        print('Error connecting to server')
        raise
    return unpack_json(resp.json())

LOG('Starting')
if len(sys.argv)>=2:
    syms = [s.upper() for s in sys.argv[1:]]
else:
    LOG('No symbol specified, defaulting to BTC;')
    #LOG(' usage: >price2 SYMBOL')
    syms = ['BTC']


for sym in syms:
    ################################################################################
    # Pull data

    LOG('Retrieving %s price history'%sym)
    prices = [*public_call('OHLC',pair=sym+'USD',interval=str(interval)).values()][0]
    cols   = 'time open high low close vwap volume count'.split()
    prices = pd.DataFrame(prices,columns=cols)
    LOG('Last recorded closing price is '+prices.close.values[-1])

    LOG('Retrieving latest price')
    ticker = public_call('Ticker',pair=[sym+'USD'])
    ticker = pd.DataFrame(ticker).T
    price  = float(ticker['c'].values[0][0]) 
    
    print(reset+hidecursor,flush=True,end='')
    LOG('Current price of %s is $%0.2f'%(sym,price))

    ################################################################################
    # Prepare chart

    # Get low and high of each interval
    h = float32(prices.high.values)
    l = float32(prices.low.values)

    # Guess label size
    fmt        = '%0.2f' if np.min(l)<=10 else '%d'
    labelwidth = max(len(fmt%np.min(l)),len(fmt%np.max(h)))+1
    plotwidth  = columns - labelwidth 

    # Plot on log-scale
    h = log10(h)[-plotwidth-1:]
    l = log10(l)[-plotwidth-1:]

    # Get y axis range
    ymin   = np.min(l)
    ymax   = np.max(h)
    yrange = ymax-ymin
    if not ymin<ymax or np.any(l>h):
        LOG('Error: minimum price is not smaller than maximum;'
            ' Is something wrong with the price data?')
        LOG('Exiting')
        sys.exit(-1) 

    '''
    We need to scale things very carefully. There are NROWS of text allocated for
    the plot. The legacy computing line shading characters define four height levels
    per line. However, the top and bottom levels for each line are one and the same.
    This means we have three levels for each row, plus one extra level for the top
    of the topmost row.
    '''

    NLEVELS = NROWS*3+1

    '''
    Quantize the signal to occupy exactly NLEVELS. The lowest value should be 0
    and the largest should be NLEVELS-1.

    The other caveat is that the upper curve (high price) must be sufficiently far
    above the lower curve (low price), so that their block-drawing characters do
    not overlap. We define the levels for the box drawing characters as follows:

        3 +----+
        2 +    +
        1 +    +
        0 +----+

    How can we tell whether the (quantized) curves occupy a particular block, and
    tweak the values to ensure this cannot happen. (The alternative would be to
    handle this in the plotting code, which I don't want to try at the moment). 

    Levels 1 and 2 will always occupy the blocks to the left/right. Level 0/3 will
    occupy blocks above or below depending on nearby values. 

    Probably the most sensible thing to do is to alternate between the high/low 
    signals, nudge any points up/down that are too close, and iterate until all
    collisions are removed. 

    Considering the upper curve first, how can we calculate the lowest text line
    needed to draw each column? First, take the minimum of each adjacent pair of
    points. Call this value N. Then consider these scenarios: 

    - If N%3 is 1 or 2, then I think N//3 is the lowest occupied block
    - if N%3 is 0, ... N//3 is still the lowest block. Ok!

    Now, there is an issue with the lower curve. We can take the maximum of adjacent
    pairs, but need to round in the opposite direction. Here, a level of 0 does not
    overlap the block above. It's also ok for the lower curve to use row -1, since
    this corresponds to the high/low band touching the lower y-axis limit.

    Further details on this procedure are in the commonts below.

    The final subtlety is that we need to avoid drawing the upper portion of the
    lower curve enturely if it would result in a █ block? 
    '''

    # Quantize signals
    qh = int32((NLEVELS-1)*(h-ymin)/yrange)
    ql = int32((NLEVELS-1)*(l-ymin)/yrange)

    assert np.all(ql<=qh)
    assert np.min(ql)==0
    assert np.max(qh)==NLEVELS-1

    # Trim things: ensure line width always >0
    ql = np.minimum(ql, np.maximum(0,qh-1))

    # Repair collisions
    for ic in range(100):

        # Blocks required to draw upper curve
        qh_mins   = np.minimum(qh[1:],qh[:-1])
        qh_blocks = qh_mins//3
        qh_levels = qh_mins%3

        # Blocks required to draw lower curve
        ql_maxs   = np.maximum(ql[1:],ql[:-1])
        ql_blocks = ql_maxs//3
        ql_levels = ql_maxs%3
        ql_blocks[ql_levels==0] -= 1
        ql_levels[ql_levels==0]  = 3

        # The following columns contain a collision
        collisions = np.where(ql_blocks >= qh_blocks)[0]
        if len(collisions)<=0: break

        # Alternate adjusting upper, lower curves, until collisions resolves
        if ic%2:
            # It's safe to assume that the lower of two adjacent upper bounds is 
            # responsible for this collision. Or both, if they are equal. So we want to
            # nudge these down a bit to see if it helps. But we wont go below 0
            qh_whichmin = np.argmin([qh[:-1],qh[1:]],axis=0)[collisions]
            qh[collisions + qh_whichmin] += 1
            qh = np.minimum(NLEVELS-1,qh)
        else:
            # It's safe to assume that the higher of two adjacent lower bounds is 
            # responsible for this collision. Or both, if they are equal. So we want to
            # nudge these down a bit to see if it helps. But we wont go below 0
            ql_whichmax = np.argmax([ql[:-1],ql[1:]],axis=0)[collisions]
            ql[collisions + ql_whichmax] -= 1
            ql = np.maximum(0,ql)
        
    '''
    Now, prepare the plot labels. We can use the horizontal one-eigth block 
    characters to draw horizontal lines on the graph We should try to make the y
    axis tick labels match these as quantitatively as possible. 

    There are 8 distinct levels per block. We should assign them
    to the centers of 8 equal divisions of the vertical interval. We will use 
    element 4 (start counting at 0), "🭸".

    We calculate how far above from the bottom of each blcok each tick is, in the
    original coordinates. We then add this to the location of the lower limits of
    each text row. 
    '''

    # Achieve faithful y tick labels
    line_offset    = 4
    range_per_step = yrange / NLEVELS
    line_height    = range_per_step*4
    divisions      = linspace(0,line_height,9)
    centers        = (divisions[1:]+divisions[:-1])/2
    tickoffset     = centers[line_offset]

    # Generate y tick labels
    yticks = linspace(ymin,ymax,NROWS+1)[:-1] + tickoffset
    labels = [labelcolor+(fmt%(10**i)).rjust(labelwidth) for i in yticks]

    '''
    Finally, plot the high/low curves on a canvas. 
    '''

    CHLAYER = 0
    BGLAYER = 1
    FGLAYER = 2

    def fill_below(
            signal, # Signal to plot (integers)
            canvas, # Numpy string array acts as a canvas 
            fgc    = fg(linecolor),
            bgc    = bgcolor,
            infill = None, 
            major  = None
        ):

        if infill is None:
            infill = ('█', bgc, fgc)

        for i in range(len(signal)-1):
            a ,b  = signal[i:i+2]
            ba,bb = a//3 ,b//3
            ta,tb = a %3 ,b %3

            # Fill regions below the plot
            canvas[:min(ba,bb),i,:] = infill
            if major:
                canvas[:min(ba,bb):4,i,:] = major

            # Fill in the "lines"
            if bb>ba and tb==0: bb,tb = bb-1,3
            if bb<ba and ta==0: ba,ta = ba-1,3
            if ba==bb:
                # Move within current text line
                index = ta*4+tb
                if index:
                    canvas[min(ba,bb),i,:] =\
                        (' 🭈🭊◢🬽🬭🭆🭄🬿🭑🬹🭂◣🭏🭍█'[index], bgc, fgc)
            else:
                # Go up or down text lines, respectively
                if bb>ba:
                    start, middle, end = '🭅🭃🭁','▐',' 🭇🭉🭋'
                else:
                    start, middle, end = '🭐🭎🭌','▌',' 🬼🬾🭀'
                    bb,ba,tb,ta = ba,bb,ta,tb
                if tb:
                    canvas[bb,i]  = (end[tb]  ,bgc,fgc)
                canvas[ba,i]      = (start[ta],bgc,fgc)
                canvas[ba+1:bb,i] = (middle   ,bgc,fgc)
        return canvas

    def fill_above(
            signal, # Signal to plot (integers)
            canvas, # Numpy string array acts as a canvas 
            fgc    = fg(linecolor),
            bgc    = bgcolor,
            infill = None, 
            major  = None
        ):

        if infill is None:
            infill = ('█', bgc, fgc)

        for i in range(len(signal)-1):
            a ,b  = signal[i:i+2]
            ba,bb = a//3 ,b//3
            ta,tb = a %3 ,b %3

            # Fill regions below the plot
            canvas[:min(ba,bb),i,:] = infill
            if major:
                canvas[:min(ba,bb):4,i,:] = major

            # Fill in the "lines"
            if bb>ba and tb==0: bb,tb = bb-1,3
            if bb<ba and ta==0: ba,ta = ba-1,3
            if ba==bb:
                # Move within current text line
                index = ta*4+tb
                if index:
                    ch = '█🭞🭠◤🭓🬎🭜🭚🭕🭧🬂🭘◥🭥🭣 '[index]
                    canvas[min(ba,bb),i,:] = (ch, bgc, fgc)
            else:
                # Go up or down text lines, respectively
                if bb>ba:
                    start, middle, end = '🭛🭙🭗','▌','█🭝🭟🭡'
                else:
                    start, middle, end = '🭦🭤🭢','▐','█🭒🭔🭖'
                    bb,ba,tb,ta = ba,bb,ta,tb
                if tb:
                    canvas[bb,i]  = (end[tb]  ,bgc,fgc)
                canvas[ba,i]      = (start[ta],bgc,fgc)
                canvas[ba+1:bb,i] = (middle   ,bgc,fgc)
        return canvas

    # Initialize canvas; 3 dimensions are: characters, background code, foreground code
    canvas = np.empty([NROWS, plotwidth, 3], dtype="U16")

    # Draw background lines
    canvas[:,:,:]   = ("┈", bgcolor, minor_line_color)
    canvas[::4,:,:] = ("─", bgcolor, minor_line_color)

    # Fill color below the high price limit
    fill_below(qh, canvas)

    # Shade graph below low price limit, mimicking the background horizontal lines
    fill_above(ql, canvas, 
        fgc    = fg(fill_color),
        bgc    = bg(linecolor), 
        infill = ('┈',bg(fill_color),minor_line_color_filled),
        major  = ('─',bg(fill_color),major_line_color_filled))

    # This used to be colored but they slowed things down
    # Combine characters and color codes
    lines = []
    for r in range(NROWS):
        ch,bc,fc = canvas[r,0,:]
        # Start with the first character
        line = ch
        for c in range(1,plotwidth):
            ch,bc,fc = canvas[r,c,:]
            line += ch
        lines.append(line)

    # Merge canvas into strings for each line
    plot = '\n'.join([r+l for l,r in zip(labels,lines)][::-1])

    # Prepare x axis and x axis tick artwork
    nxblocks = int(ceil(columns/6))
    xaxis    = ''.join(('──────',)*3)+''.join(('─────┬',)*(nxblocks-3))
    xaxis    = xaxis[len(xaxis)-plotwidth:-1] + '┐' + ' '*labelwidth

    # Prepare x axis label and x tick labels
    xlabel = "Hours ago:  "
    xticks = [str(i).rjust(6) for i in int(3*interval/30)*arange(nxblocks)[::-1]]
    xticks[0] = ' '*6
    xticks = ''.join(xticks)
    xticks = xticks[len(xticks)-columns+labelwidth:]
    xticks = xlabel + xticks[len(xlabel):]

    # Patch some of the symbols

    # Show plot
    sys.stdout.write(labelcolor+plot+'\n'+xaxis+'\n'+xticks+rs.all+'\n')
    sys.stdout.flush()

print(showcursor,end='')
