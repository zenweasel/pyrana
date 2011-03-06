import dbus

from feather import Plugin

class PidginStatus(Plugin):
    listeners = set(['songstart', 'songpause', 'songresume'])
    messengers = set()

    def songstart(self, payload):
        #hacky.
        parts = payload.split('/')
        artist = parts[-3]
        album = parts[-2]
        song = parts[-1]
        self.song_msg = "%s (%s): %s" % (artist, album, song)

        self.update_status(self.song_msg)

    def pause(self, payload=None):
        self.update_status("Paused")

    def resume(self, payload=None):
        self.update_status(self.song_msg)

    def update_status(self, msg):
        bus = dbus.SessionBus()

        if "im.pidgin.purple.PurpleService" in bus.list_names():
            purple = bus.get_object("im.pidgin.purple.PurpleService",
                                    "/im/pidgin/purple/PurpleObject",
                                    "im.pidgin.purple.PurpleInterface")
            current = purple.PurpleSavedstatusGetType(
                purple.PurpleSavedstatusGetCurrent())
            status = purple.PurpleSavedstatusNew("", current)
            purple.PurpleSavedstatusSetMessage(status, msg)

            purple.PurpleSavedstatusActivate(status)
