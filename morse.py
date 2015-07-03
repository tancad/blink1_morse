#!/usr/bin/env python3
import time, sys, os, subprocess, argparse
import webcolors

# SET TO BLINK TOOL PATH
BLINK_TOOL_PATH = "blink1-tool"

# Set to delay inherent in calling blink1-tool (default 50 ms)
BLINK_TOOL_DELAY = 50

morsetab = {
        'A': '.-',              'a': '.-',
        'B': '-...',            'b': '-...',
        'C': '-.-.',            'c': '-.-.',
        'D': '-..',             'd': '-..',
        'E': '.',               'e': '.',
        'F': '..-.',            'f': '..-.',
        'G': '--.',             'g': '--.',
        'H': '....',            'h': '....',
        'I': '..',              'i': '..',
        'J': '.---',            'j': '.---',
        'K': '-.-',             'k': '-.-',
        'L': '.-..',            'l': '.-..',
        'M': '--',              'm': '--',
        'N': '-.',              'n': '-.',
        'O': '---',             'o': '---',
        'P': '.--.',            'p': '.--.',
        'Q': '--.-',            'q': '--.-',
        'R': '.-.',             'r': '.-.',
        'S': '...',             's': '...',
        'T': '-',               't': '-',
        'U': '..-',             'u': '..-',
        'V': '...-',            'v': '...-',
        'W': '.--',             'w': '.--',
        'X': '-..-',            'x': '-..-',
        'Y': '-.--',            'y': '-.--',
        'Z': '--..',            'z': '--..',
        '0': '-----',           ',': '--..--',
        '1': '.----',           '.': '.-.-.-',
        '2': '..---',           '?': '..--..',
        '3': '...--',           ';': '-.-.-.',
        '4': '....-',           ':': '---...',
        '5': '.....',           "'": '.----.',
        '6': '-....',           '-': '-....-',
        '7': '--...',           '/': '-..-.',
        '8': '---..',           '(': '-.--.-',
        '9': '----.',           ')': '-.--.-',
        ' ': ' ',               '_': '..--.-',
}

class InvalidColor(ValueError):
    """Raised when the user requests an implausible colour
    """

def translateText(ascii_text):
    '''
    Translate ASCII input to morse code
    Uses the translation table above
    not included characters are ignored
    '''
    morse_output = []
    for c in ascii_text:
        if c in morsetab:
            morse_output.append(morsetab[c])
    return morse_output

def translateMorse(morse_array,base_length=100,color="255,255,255",shift_color=False,target_color="255,255,255"):
    '''
    Send the morse code out to the blink(1). Accepts up to 5 arguments:
    1. morse_array: Text translated to morse by translateText() method
    2. base_length: The base duration for a dit in milliseconds. All other lengths are calculated by this base length
    3. color: The color the morse code should have. If shifting colors are used this is the starting color
    4. shift_color: True/False, if True tries to shift the color over all blinks to target_color
    5. Only used if shift_color = True, this color should (more or less) be reached at the last blink
    '''
    base_color = color_to_rgb(color)
    target = color_to_rgb(target_color)
    number_blinks = numberBlinks(morse_array)
    new_color = base_color
    mod_r, mod_g, mod_b = colorDiff(base_color,target,number_blinks)
    blink_counter = 0
    for character in morse_array:
        if character == " ":
            print("space")
            waitEmit(base_length*4+BLINK_TOOL_DELAY)
        else:
            for j in character:
                if shift_color == True and blink_counter > 0:
                    new_color = newColor(new_color,[mod_r,mod_g,mod_b],target,blink_counter)
                if j == "-":
                    emitDit(base_length,new_color,dah=True)
                elif j == ".":
                    emitDit(base_length,new_color)
                blink_counter += 1
            waitEmit(base_length*3)

def newColor(color,modulos,target,blink_counter):
    color_array = splitColor(color)
    out_color = []
    for i,single_color in enumerate(color_array):
        if color_array[i] < target[i]:
            out_color.append(min(color_array[i] + abs(modulos[i]),255))
        elif color_array[i] > target[i]:
            out_color.append(max(color_array[i] - abs(modulos[i]),0))
        else:
            out_color.append(color_array[i])
    colors = ",".join([str(i) for i in out_color])
    return colors    

def color_to_rgb(color):
    if isinstance(color, tuple):
        return color
    if not color.startswith('#'):
        try:
            return splitColor(color)
        except InvalidColor:
            pass
    if len(color) == 6:
        color = '#' + color
    if color.startswith('#'):
        try:
            return webcolors.hex_to_rgb(color)
        except ValueError:
            raise InvalidColor(color)
    try:
        return webcolors.name_to_rgb(color)
    except ValueError:
        raise InvalidColor(color)
    else:
        raise InvalidColor(color)

def splitColor(color):
    '''
    Take color input in blink(1)-tool-format and 
    return as list with each value as integer 
    '''
    if len(color.split(",")) != 3:
        raise InvalidColor(color)
    colors = ()
    for c in color.split(","):
        colors += (int(c),)
    
    return colors

def colorDiff(base,target,number_blinks):
    '''
    Takes start color, end color and number of total blinks in text. 
    Returns how much each color value has to be shifted in a given blink 
    '''
    color_difference = []
    for i,value in enumerate(target):
        diff = int(round(float(value-base[i])/max(number_blinks-1,1)))
        if diff == 0:
            diff = 1
        color_difference.append(diff)
    return color_difference[0], color_difference[1], color_difference[2]
    

def numberBlinks(morse_array):
    '''
    Calculate how many times the blink(1) will have to emit a blink.
    Needed to calculate the color shifting frequency
    '''
    length = 0
    for i in morse_array:
        if i != " ":
            length += len(i)
    return length
            
def waitEmit(length):
    '''
    We don't want to send a signal, just wait to be in line with morse specs
    '''
    #print "wait " + str(length)
    if length > BLINK_TOOL_DELAY:
        time.sleep(float(length-BLINK_TOOL_DELAY)/1000)

def emitDit(dit_length,color,dah=False):
    '''
    Lights please! Either a dit or a dah (3*time of dit)
    '''
    command = BLINK_TOOL_PATH + ' --rgb "'+webcolors.rgb_to_hex(color)+'" -m 0 '
    print((command), end=' ')
    output = subprocess.call(command, stdout=subprocess.PIPE, shell=True)
    if dah==True:
        print("(dah)")
        time.sleep(float(dit_length*3)/1000)
    else:
        print("(dit)")
        time.sleep(float(dit_length)/1000)
    command_off = BLINK_TOOL_PATH + " --off -m 0"
    output = subprocess.call(command_off, stdout=subprocess.PIPE, shell=True)
    waitEmit(dit_length)

def main():
    '''
    Parse arguments & run stuff if run from script
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("text",type=str,help="This is the text that should be emitted")
    parser.add_argument("-c","--color",type=str,default="255,255,255",help="The (initial) color of the blinks. Specify as R,G,B. Default: 255,255,255")
    parser.add_argument("-s","--shift",action="store_true",help="Should the color shift? If yes: --target-color needs to be specified")
    parser.add_argument("-tc","--target-color",type=str,default="255,255,255", help="The final color of the blinks. Specify as R,G,B. Default: 255,255,255")
    parser.add_argument("-t","--time", type=int, default=100, help="Duration of a single dit in milliseconds. Default: 100") 
    args = parser.parse_args()
    print(args)
    morse_text = translateText(args.text)
    translateMorse(morse_text,base_length=args.time,color=args.color,shift_color=args.shift,target_color=args.target_color)

if __name__ == "__main__":
    main()