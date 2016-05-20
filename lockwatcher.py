#!/usr/bin/env python3
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from timekeeper import db


SQLITE_FILE = '/home/antonopa/.timekeeper.sqlite'


def handle_lock(LockState):
    """ ActiveChanged signal from org.gnome.ScreenSaver is emitted whenever
        a user lock or unlocks their system. We use this to update our DB.
        Since INSERT only inserts a day if it doesn't exist only the first
        unlock (LockState False) in a day will insert an entry.
        Every lock (LockState True) updates the DB with the current time and
        as a result last lock marks the end of the work day.
    """
    with db.__Sqlite(SQLITE_FILE) as tk:
        if LockState:
            # System locked
            tk.update_end(day='now', end='now')
        else:
            # System unlocked
            tk.insert_day('now')


SIGNALS = {
    'ActiveChanged':
    {'service':'org.gnome.ScreenSaver', 'iface':'org.gnome.ScreenSaver', 'method':handle_lock }
}


def attach_to_signal(name, properties ):
    """ Attach method to a DBus signal """
    bus = dbus.SessionBus()
    bus.add_signal_receiver(
            properties['method'], signal_name=name,
            dbus_interface=properties['iface'], bus_name=properties['service'])

if __name__ == "__main__":
    DBusGMainLoop(set_as_default=True)
    loop = GLib.MainLoop()

    for signal, properties in SIGNALS.items():
        attach_to_signal(signal, properties)

    loop.run()

