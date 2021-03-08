import os   #os.system('')
import RPi.GPIO as GPIO
import time
import pyttsx3  #relies on espeak
#import pyautogui
from pygame import mixer
from pynput import keyboard   #for monitoring the keyboard (listening)
from pynput.keyboard import Key, Controller
import random


# === 1. Remap some keys for the RF remote control
os.system('xmodmap -e "keycode 20 = XF86AudioLowerVolume"')  # '-'
os.system('xmodmap -e "keycode 21 = XF86AudioRaiseVolume"') # '='
os.system('xmodmap -e "keycode 9 = XF86AudioMute"')  # 'ESC / home'
os.system('xmodmap -e "keycode 136 = XF86AudioMute"') # 'STOP'
os.system('xmodmap -e "keycode 172 = XF86AudioMute"') # 'playpause'
# setxkbmap

engine = pyttsx3.init()
engine.setProperty('volume',1.0)
engine.setProperty('rate', 150)
time.sleep(0.5)
engine.say('Hello Mr. Weber, this is the python script running at reboot time.')
engine.runAndWait()

# === 2. Startup the Music Player
#1. get all music files in a directory
music_dir = '/home/pi/Desktop/worship'
music_files = []
#get non-directory files, with extension='.mp3' (note:extensions can be capitalized)
for fileName in os.listdir(music_dir):
    #print(fileName)
    if (os.path.isdir(music_dir+fileName) == False): #if NOT a directory:
        fileExtension = os.path.splitext(fileName)[1] #splitext gives: [basename, ext]
        #print(fileExtension)
        if (fileExtension.lower() == '.mp3'): #extensions can be capitalized
            music_files.append(fileName)


#play/pause, 
#next song,rewind/previous-song,
#shuffle, repeat, skip through song, get information
#print(music_files)
total_songs = len(music_files)
current_song_index = 0
shuffle = 'off'
repeat = 'off'
isPaused = False

def shuffleMusicList():
    global current_song_index
    random.shuffle(music_files)
    #should we update the current_song_index?? I probably should, but currently,
    #it doesn't break anything, I think.
        
def getValidIndex(currentIndex, nextOrPrev):
    if (nextOrPrev == 'next'):
        if (currentIndex >= (len(music_files) - 1)):
            return 0
        else:
            return (currentIndex + 1)
    elif (nextOrPrev == 'prev'):
        if (currentIndex <= 0):
            return (len(music_files) - 1)
        else:
            return (currentIndex - 1)

def doNextSong(nextOrPrev):
    global current_song_index
    #1. determine index of next song
    next_song = getValidIndex(current_song_index, nextOrPrev)
    nextnextsong = getValidIndex(next_song, 'next')
    #2. queue up the next-next song
    mixer.music.load(os.path.join(music_dir,music_files[next_song]))
    mixer.music.queue(os.path.join(music_dir,music_files[nextnextsong]))
    mixer.music.set_volume(0.8)
    mixer.music.play()
    current_song_index = next_song
    print(music_files[current_song_index])
    
        
mixer.init()
mixer.music.set_volume(0.8)
mixer.music.load(os.path.join(music_dir,music_files[current_song_index]))
next_song = getValidIndex(current_song_index, 'next')
mixer.music.queue(os.path.join(music_dir,music_files[next_song]))
mixer.music.play()
#pygame.event.wait()  not needed...

newKeyboard = Controller()
def on_press(key):
    try:
        #engine.say('alphanumeric key {0} pressed'.format(key.char))
        #engine.runAndWait()
        print('alphanumeric key {0} pressed'.format(key.char))
    except AttributeError:
        print('special key {0} pressed'.format(key))
        
def on_release(key):
    global isPaused, current_song_index
    #if do an assignment to a var inside a func, python assumes var is local
    print('{0} released'.format(key))
    if key == keyboard.Key.esc:  #home button
        print('home')
    elif key == keyboard.Key.left:
        print('left')
        doNextSong('prev')
    elif key == keyboard.Key.right:
        print('right')
        doNextSong('next')
    elif key == keyboard.Key.up:
        print('up')
        mixer.music.rewind()
    elif key == keyboard.Key.down:
        print('down')
        #current_pos = mixer.music.get_pos() / 1000 #milliseconds/1000 = seconds
        #mixer.music.set_pos(current_pos+10)  #jump forward 10 seconds
    elif key == keyboard.Key.enter:
        print('enter')
        if (isPaused):
            print('unpausing...')
            mixer.music.unpause()
            isPaused = False
        else:
            print('pausing...')
            mixer.music.pause()
            isPaused = True
            
    else:
        try:  #key.char could be undefined. 
            if key.char == 'i':  #info
                print('info')
                engine.say(os.path.splitext(music_files[current_song_index])[0])
                engine.runAndWait()
            elif key.char == 'c':  #list icon
                print('list icon')
                shuffleMusicList()
        except AttributeError:
            print('end')


listener = keyboard.Listener(
    on_press=on_press,
    on_release=on_release)
listener.start()


# === 3. Listen for legitimate signal from doorbell/door-alarm receiver
# (if >40 consecutive light measurements, send a hotkey to pause the music)
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def receivedSignal():
    #
    global isPaused
    mixer.music.pause()
    isPaused = True
    #engine.say('Door is open.')
    #engine.runAndWait()

consecutive_measurements = 0  #counter for consecutive measurements of light
previous_measure = 0
print('running the GPIO loop...')
while True:
    if GPIO.input(18) == 0:
        #print("it's light out, "+str(counter))
        if (previous_measure == 1):
            consecutive_measurements = consecutive_measurements + 1
            if (consecutive_measurements > 30):
                receivedSignal()
        else:
            #print("light on")
            previous_measure = 1
    else:
        #print("it's dark out, "+str(counter))
        previous_measure = 0
        consecutive_measurements = 0  #reset counter
    time.sleep(.01)


GPIO.cleanup()
print("end of runtime")


# GPIO 18 (top row 6th) and Ground (top row 3rd) (orientation: PWR input bottom right)
# longer lead = positive, shorter lead = ground
# the action is to lower or mute the system volume
# figure out how to do this from a python script