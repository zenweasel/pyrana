#!/usr/bin/env python
"""
Pyrana -- a minimalist music player.

This program was written out of frustration with larger music players. Pretty
much all I've ever wanted out of a music player was one that played random
albums by picking a random artist, then picking a random album, then playing
that album, then picking _another random artist_.

For some reason,I've never run into a music player that played random albums
that way, which led to me often ending up having to skip past multiple Frank
Zappa albums when playing random albums. I like Zappa, but not that goddamned
much. Same deal with Slayer and Aphex Twin and Bad Religion, and all these
other artists and bands that I have discographies of.

Another problem I've had is that a lot of 'modern' music players base their
artist and album information off of metadata. I have a couple of issues with
this:

1: My music collection is large. Doing a scan of metadata, even if it only
needs to be done once takes a long time. I hate it.

2: My music collection has unreliable metadata. This is because I'm a lazy
asshole, and haven't kept up with fixing metadata on music that I
download. That's right, I download music -- so do you, shut up. My music
collection is so large that the probability of me fixing the metadata ever is
basically nil. I can, however, rely on the directory structure of my music
collection.

This little program does one thing, and does it acceptably -- play random
albums from a music collection. Maybe it'll expand in the future to include
things like last.fm support. Maybe.
"""


import os
import random
import ConfigParser

import pygst
pygst.require("0.10")
import gst

import pygtk
pygtk.require('2.0')
import gtk

import pynotify
pynotify.init("Basics")


class Pyrana(object):
    """Our player, sending sweet, sweet sounds to our speakers.
    """

    def __init__(self):
        """Initialize our player with a root directory to search through for
        music, and start the gtk main thread.
        """
        self.base_path = os.path.dirname(os.path.realpath(__file__))

        self.status_icon = gtk.StatusIcon()
        self.status_icon.connect('activate', self.on_left_click)
        self.status_icon.connect('popup-menu', self.on_right_click)
        self.status_icon.set_visible(True)
        self.status_icon.set_tooltip("Pyrana!")
        self.status_icon.set_from_file(os.path.join(self.base_path,'stopped.png'))
        
        self.menu = gtk.Menu()
        skip_song = gtk.MenuItem("Skip Song")
        skip_album = gtk.MenuItem("Skip Album")
        quit_app = gtk.MenuItem("Quit")
        self.menu.append(skip_song)
        self.menu.append(skip_album)
        self.menu.append(quit_app)

        skip_song.connect_object("activate", self.skip_song, "Skip Song")
        skip_album.connect_object("activate", self.skip_album, "Skip Album")
        quit_app.connect_object("activate", self.quit, "Quit")
        
        skip_song.show()
        skip_album.show()
        quit_app.show()
        
        self.config = ConfigParser.ConfigParser()
        self.config.read(os.path.join(self.base_path, 'pyrana.cfg'))

        self.pidgin_status = self.config.get('main',
                                             'update_pidgin_status')
        self.use_notify = self.config.get('main', 'use_notify')
        
        #give us a list of sets of albums by artists, assuming the directory
        #structure
        #Artists
        # Albums
        #  Songs
        #This is a little ugly, but whatever.
        root = os.path.expanduser(
            self.config.get('main', 'music_dir'))
        self.artists = [[os.path.join(artist, album)
                             for album in os.listdir(artist)
                             if os.path.isdir(os.path.join(artist, album))]
                        for artist in
                        [os.path.join(root, artistname)
                         for artistname in os.listdir(root)
                         if os.path.isdir(os.path.join(root, artistname))]]

        #just in case we get some empty directories
        self.artists = [a for a in self.artists if a]

        self.player = gst.element_factory_make("playbin2", "player")

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect('message::eos', self.on_eos)

        self.playing = False
        self.cur_song = None
        self.cur_album = None
        self.cur_artist = None
        
        gtk.main()

    def on_eos(self, bus, msg):
        self.player.set_state(gst.STATE_NULL)
        self.cur_song = None
        self.playing = False
        self.on_left_click(None)
        
    def on_left_click(self, widget, data=None):
        """Click handler for our status icon. Play or stop playing,
        respectively.
        """
        if not self.playing:
            self.playing = True
            self.status_icon.set_from_file(
                os.path.join(self.base_path, 'playing.png'))
            if not self.cur_song:
                self.cur_song = self.get_next_song()
                self.player.set_property('uri', 'file://%s' % self.cur_song)
            self.player.set_state(gst.STATE_PLAYING)
            self.status_icon.set_tooltip(self.cur_song)
            if self.use_notify:
                self.notify(self.cur_song)
            if self.pidgin_status:
                self.update_pidgin_status(self.cur_song)
            
        else:
            self.player.set_state(gst.STATE_PAUSED)
            self.playing = False
            self.status_icon.set_from_file(os.path.join(
                    self.base_path, 'stopped.png'))
            self.status_icon.set_tooltip("[PAUSED] %s" % self.cur_song)
            
    def on_right_click(self, data, event_button, event_time):
        self.menu.popup(None, None, None, event_button, event_time)

    def get_next_song(self):
        if not self.cur_album:
            artist = self.cur_artist
            
            while artist == self.cur_artist:
                artist = random.choice(self.artists)
                
            albumpath = artist.pop(random.randrange(len(artist)))
            self.cur_album = sorted([os.path.join(albumpath, song)
                                     for song in os.listdir(albumpath)])
        song = self.cur_album[0]
        self.cur_album = self.cur_album[1:]
        return song

    def skip_song(self, data=None):
        self.on_eos(None, None)

    def skip_album(self, data=None):
        self.cur_album = None
        self.on_eos(None, None)

    def quit(widget, data=None):
        gtk.main_quit()

    def notify(self, songpath):
        """Use libnotify to show growl-like alerts about what's playing.
        """
        to_display = "Playing: %s" % songpath
        notification = pynotify.Notification("Pyrana", to_display)
        notification.show()
    
    def update_pidgin_status(self, songpath):
        import dbus
        bus = dbus.SessionBus()
        parts = songpath.split('/')

        artist = parts[-3]
        album = parts[-2]
        song = parts[-1]
        
        if "im.pidgin.purple.PurpleService" in bus.list_names():
            purple = bus.get_object("im.pidgin.purple.PurpleService",
                                    "/im/pidgin/purple/PurpleObject",
                                    "im.pidgin.purple.PurpleInterface")
            current = purple.PurpleSavedstatusGetType(
                purple.PurpleSavedstatusGetCurrent())
            status = purple.PurpleSavedstatusNew("", current)
            purple.PurpleSavedstatusSetMessage(status,
                                               "%s (%s): %s" %
                                               (artist, album, song))
            purple.PurpleSavedstatusActivate(status)

if __name__ == '__main__':
    import sys
    Pyrana()
