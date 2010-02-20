#!/usr/bin/env python
"""
Pyrana -- a minimalist music player.

This little script was written out of frustration with larger music
players. Pretty much all I've ever wanted out of a music player was one that
played random albums by picking a random artist, then picking a random album,
then playing that album, then picking _another random artist_.

For some reason,I've never run into a music player that played random albums
that way, which led to me often ending up having to skip past multiple Frank
Zappa albums when playing random albums. I like Zappa, but not that goddamned
much. Same deal with Slayer and Aphex Twin and Bad Religion, and all these other
artists and bands that I have discographies of.

Another problem I've had is that a lot of 'modern' music players base their
artist and album information off of metadata. I have a couple of issues with this:

1: My music collection is large. Doing a scan of metadata, even if it only needs
to be done once takes a long time. I hate it.

2: My music collection has unreliable metadata. This is because I'm a lazy
asshole, and haven't kept up with fixing metadata on music that I
download. That's right, I download music -- so do you, shut up. Since my music
collection is so large that the probability of me fixing the metadata ever is
basically nil. I can, however, rely on the directory structure of my music
collection.

This little ~50 line does one thing, and does it acceptably -- play random
albums from a music collection. Maybe it'll expand in the future. I doubt it.
"""
import os
import random
import time
import ConfigParser
import pygame.mixer as mixer

config = ConfigParser.ConfigParser()
config.read('pyrana.cfg')

def notify(songpath):
    to_display = "Playing: %s" % songpath
    if config.get('main', 'notification_type') == 'pynotify':
        import pygtk
        pygtk.require('2.0')
        import pynotify
        pynotify.init("Basics")
        n = pynotify.Notification("Pyrana", to_display)
        n.show()
    else:
        print to_display


def play(root, frequency=44100):
    mixer.init(frequency)
    #give us a list of sets of albums by artists, assuming the directory structure
    #Artists
    # Albums
    #  Songs
    #This is a little ugly, but whatever. 
    artists = [set([os.path.join(artist, album)
                   for album in os.listdir(artist)
                   if os.path.isdir(os.path.join(artist, album))])
              for artist in [os.path.join(root, artistname)
                             for artistname in os.listdir(root)
                             if os.path.isdir(os.path.join(root, artistname))]]

    #just in case we get some empty directories
    artists = filter(None, artists)

    while artists:
        artist = random.choice(artists)

        #this ensures that we never play the same album twice
        albumpath = artist.pop()

        #hopefully, the tracks will be named in such a way that we can rely
        #on their names for ordering 
        album = sorted([os.path.join(albumpath, song)
                        for song in os.listdir(albumpath)
                        if song.endswith('mp3')])
        while album:
            if not mixer.music.get_busy():
                songpath = album[0]
                album = album[1:]
                notify(songpath)
                mixer.music.load(songpath)
                mixer.music.play()
            else:
                #avoid eating cpu
                time.sleep(1)

        artists = filter(None, artists)

if __name__ == '__main__':
    import sys
    play(sys.argv[1])
