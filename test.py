#!/usr/bin/python3.8

import random
import threading
import asyncio
from rpilcdmenu import *
from rpilcdmenu.items import *

menu = RpiLCDMenu()
eventLoop = asyncio.get_event_loop()
inVolume=False
gInputClock = 0

# This is called in our main thread .. in FIFO order with everything else
def onRotaryEvent(data):
    global gInputClock
    gInputClock += 1

    print("We got a rotary event: %s" % (data, ))

    # render the menu

    menuTopText ='Really Looooooong Menu Item %d' % (random.randint(1000,21000), )
#    menuTopText = 'Top Menu'
    menuBottomText ='Short Menu'

    # Each line to be rendered goes into a list
    menuText = [menuTopText, menuBottomText]

    eventLoop.create_task(onRenderMenuItem(gInputClock, menuText))


##########################################################################################
# Menu Rendering
##########################################################################################

# co-routine to handle menu scrolling animation
#   This always runs on the main thread, processed in-line with the input events, but
#   behind the scenes, it allows other processing to continue during the calls to sleep
async def onRenderMenuItem(inputClock, text):
    maxWidth = 15

    if len(text[0]) <= maxWidth:
        # top row  of the menu fits on line.. no need to animate
        for row in text:
            line = text.index(row) + 1
            print("rendering on line %s -- %s" % (line, row[:maxWidth]))
        # We're going to truncate the bottom line if it's too long
        text = [text[0], text[1][:maxWidth]]
        menu.write_to_lcd(text)
        return

    # top line too long.. so animate until there's another input event
    aniPosition = 0
    firstFrame = True
    delta = 1
    while inputClock == gInputClock:
        ### render partial menu text
        aniText = text[0][aniPosition: aniPosition + maxWidth]
        print("rendering on line %d -- %s" % (1, aniText, ))
        # Pack current frame of top-row animation into framebuffer list with static truncated bottom row
        framebuffer = [aniText[:maxWidth], text[1][:maxWidth]]
        print(framebuffer)
        # Send the framebuffer to the LCD
        menu.write_to_lcd(framebuffer)

        ### determine next state
        aniPosition += delta
        if aniPosition >= (len(text[0]) - maxWidth):
            delta = -1
        elif aniPosition <= 0:
            delta = 1

        ### sleep, letting other co-routines run
        if firstFrame:
            await asyncio.sleep(1.5)
        else:
            await asyncio.sleep(0.15)
        firstFrame = False

#####################################################################
# set up rotatary encoder input event dispatching
#####################################################################

from pyky040 import pyky040

# simple event handler (not a co-routine)
def rotary_encoder():
    def my_deccallback(scale_position):
        if scale_position % 2 == 0:  # Trigger every 2 'rotations' as my rotary encoder sends 2 per 1 physical click
            # "marshal"/"delegate" to main event queue
            eventLoop.call_soon_threadsafe(onRotaryEvent, 'Up')

    def my_inccallback(scale_position):
        if scale_position % 2 == 0:
            # "marshal"/"delegate" to main event queue
            eventLoop.call_soon_threadsafe(onRotaryEvent, 'Down')

    def my_swcallback():
        # "marshal"/"delegate" to main event queue
        eventLoop.call_soon_threadsafe(onRotaryEvent, 'Enter')

    my_encoder = pyky040.Encoder(CLK=22, DT=23, SW=24)

    my_encoder.setup(scale_min=1, scale_max=100, step=1, loop=True, inc_callback=my_inccallback, dec_callback=my_deccallback, sw_callback=my_swcallback)
    my_encoder.watch()


############
# my simulation of rotaryEvents
import time
def simulateRawRotaryEvents():
    while True:
        time.sleep(random.uniform(2, 6))
        onRawRotaryEvent(random.choice([0, 1]))


rotaryInputThread = threading.Thread(target=rotary_encoder)
rotaryInputThread.daemon = True  # make it not stall the process at exit
rotaryInputThread.start()
############






######################################################################
# some other random processing
######################################################################

# co-routine doing other work
async def stuffToDo():
    while True:
        await asyncio.sleep(random.uniform(1, 3))  # let other co-routines run
        print("doing other stuff")

eventLoop.create_task(stuffToDo())



print("starting event loop")
eventLoop.run_forever();

# it will never get here until something calls loop.stop()
print("event loop finished")

# NOTE: we're not doing anything to "nicely" cleanup the rotary input thread
