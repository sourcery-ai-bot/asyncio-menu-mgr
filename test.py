#!/usr/bin/python3.8

import random
import threading
import asyncio

eventLoop = asyncio.get_event_loop()

gInputClock = 0

# This is called in our main thread .. in FIFO order with everything else
def onRotaryEvent(data):
    global gInputClock
    gInputClock += 1

    print("We got a rotary event: %s" % (data, ))

    # render the menu

    menuText ='Really Looooooong Menu Item %d' % (random.randint(1000,21000), )
    eventLoop.create_task(onRenderMenuItem(gInputClock, 0, menuText))

    menuText ='Short Menu'
    eventLoop.create_task(onRenderMenuItem(gInputClock, 1, menuText))




##########################################################################################
# Menu Rendering
##########################################################################################

# co-routine to handle menu scrolling animation
#   This always runs on the main thread, processed in-line with the input events, but
#   behind the scenes, it allows other processing to continue during the calls to sleep
async def onRenderMenuItem(inputClock, line, text):
    maxWidth = 15

    if len(text) <= maxWidth:
        # menu fits on line.. no need to animate
        print("rendering on line %s -- %s" % (line, text))
        return

    # line too long.. so animate until there's another input event (which perhaps it really ought to be conditioned on whether the menu has been re-rendered, regardless of user input)
    aniPosition = 0
    firstFrame = True
    delta = 1
    while inputClock == gInputClock:

        ### render partial menu text
        aniText = text[aniPosition: aniPosition + maxWidth]
        print("rendering on line %d -- %s" % (line, aniText, ))

        ### determine next state
        aniPosition += delta
        if aniPosition >= (len(text) - maxWidth):
            delta = -1
        elif aniPosition <= 0:
            delta = 1

        ### sleep, letting other co-routines run
        if firstFrame:
            await asyncio.sleep(1.5)
        else:
            await asyncio.sleep(0.1)
        firstFrame = False






#####################################################################
# set up rotatary decide input event dispatching
#####################################################################

# simple event handler (not a co-routine)
def onRawRotaryEvent(data):
    # "marshal"/"delegate" to main event queue
    eventLoop.call_soon_threadsafe(onRotaryEvent, data)

#import rotary_thing
#rotaryInput = rotary_thing.initialize(pin1, pin2, onRawRotaryEvent)
##  Set up background thread so that start() doesn't block our main thread, but marshal any events over to the asyncio event queue
#rotaryInputThread = threading.Thread(target=rotaryInput.start())
#rotaryInputThread.daemon = True  # make it not stall the process at exit
#rotaryInputThread.start()

############
# my simulation of rotaryEvents
import time
def simulateRawRotaryEvents():
    while True:
        time.sleep(random.uniform(2, 6))
        onRawRotaryEvent(random.choice([0, 1]))
rotaryInputThread = threading.Thread(target=simulateRawRotaryEvents)
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
