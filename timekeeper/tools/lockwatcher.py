#!/usr/bin/env python3
"""
Basic dbus listener to monitor locking/unlocking of screen. Unlocking tries to insert a new day
(only first insertion, aka start of day, will succeed) and locking update the end of day time
(last lock is assumed to be the time we leave the office).
"""
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from os import path

from timekeeper.worktimedb import WorkTimeDB


SQLITE_FILE = path.join(path.expanduser('~'), '.timekeeper.sqlite')


def handle_lock(lock_state):
    """ ActiveChanged signal from org.gnome.ScreenSaver is emitted whenever
        a user lock or unlocks their system. We use this to update our DB.
        Since INSERT only inserts a day if it doesn't exist only the first
        unlock (LockState False) in a day will insert an entry.
        Every lock (LockState True) updates the DB with the current time and
        as a result last lock marks the end of the work day.
    """
    with WorkTimeDB(SQLITE_FILE) as worktime:
        if lock_state:
            # System locked
            worktime.update_end(day='now', end='now')
        else:
            # System unlocked
            worktime.insert_day('now')


SIGNALS = {
    'ActiveChanged':
    {'service':'org.freedesktop.ScreenSaver', 'iface':'org.freedesktop.ScreenSaver', 'method':handle_lock}
}


def attach_to_signal(name, properties):
    """ Attach method to a DBus signal """
    bus = dbus.SessionBus()
    bus.add_signal_receiver(
        properties['method'], signal_name=name,
        dbus_interface=properties['iface'], bus_name=properties['service'])

def main():
    """ main entry """
    DBusGMainLoop(set_as_default=True)
    loop = GLib.MainLoop()

    for signal, properties in SIGNALS.items():
        attach_to_signal(signal, properties)

    loop.run()

if __name__ == "__main__":
    main()
