#!/usr/bin/env python3
"""
Command line utility to update start/end time of work days and print reports
on overtime.
"""
import argparse
from sqlite3 import OperationalError
from pprint import PrettyPrinter
import sys
from datetime import datetime
import shutil

from os import path
from timekeeper.worktimedb import WorkTimeDB


SQLITE_FILE = path.join(path.expanduser('~'), '.timekeeper.sqlite')

def handle_db_calls(provided_args):
    """ Handle all db related calls here """
    def call_retriever(func):
        """ Harvest input argument for reporting period and call the desired
            function """
        start = provided_args.start_date[0] if provided_args.start_date else None
        end = provided_args.end_date[0] if provided_args.end_date else None
        return func(start, end)

    myp = PrettyPrinter(indent=2).pprint
    __DBG = lambda _: None

    with WorkTimeDB(SQLITE_FILE) as work_time:
        if provided_args.debug:
            def dbg(x):
                PrettyPrinter(indent=2).pprint(x)
            __DBG = dbg
            __DBG("Debug on")
            __DBG(provided_args)
            work_time.debug = dbg
        if provided_args.add:
            __DBG("Add: " + provided_args.add[0])
            work_time.insert_day(provided_args.add[0])
        if provided_args.balance:
            myp(provided_args.balance)
            work_time.insert_day(
                day='now' if not provided_args.start_date else provided_args.start_date[0],
                end=datetime.now().strftime("%H:%M:%S"), lunch_duration=0)
        if provided_args.out:
            myp("Leave earliest at: " + work_time.expected_time_str())
        if provided_args.show:
            if provided_args.show >= 3:
                print("Everything: ")
                for k,v in call_retriever(work_time.get_period).items():
                    print(k)
                    print("\tStart: {}".format(v['Start']))
                    print("\tEnd:   {}".format(v['End']))
                    print("\tLeave: {}".format(v['Leave time']))
                    print("\tWork time:  {}".format(v['HH:MM']))
            if provided_args.show >= 2:
                print("Overtime per day: ")
                for k in call_retriever(work_time.get_overtime):
                    print("\t{!s}, minutes: {:4}/{}".format(*k))
            if provided_args.show >= 1:
                print("Overtime sum: %s" % call_retriever(work_time.overtime_to_str))

        if provided_args.update is not None:
            end = provided_args.update[0] if provided_args.update else 'now'
            work_time.update_end(day='now', end=end)
        if provided_args.period:
            start = provided_args.start_date[0] if provided_args.start_date else None
            end = provided_args.end_date[0] if provided_args.end_date else None
            myp(work_time.get_period(start, end))
        if provided_args.lunch:
            work_time.update_lunch(provided_args.lunch[0])
        if provided_args.custom:
            # first argument is the method call.
            # We pass everything else as arguments to that method.
            method = getattr(work_time, provided_args.custom[0], None)
            provided_args = provided_args.custom[1:]
            print(provided_args)
            if callable(method):
                myp(method(*provided_args))

def _get_args():
    """ Add all the needed arguments in ArgumentParser and return the ones with
    which this was called """
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--add", nargs='+',
                        help='Add new day in the DB')
    parser.add_argument("-o", "--out", action='store_true',
                        help='Print the end of the current work day')
    parser.add_argument("-s", "--show", action='count',
                        help='Print report. Repeat the option for more info')
    parser.add_argument("-u", "--update", nargs='*',
                        help=('Update end of today\'s work day. '
                              'Optionally provide time else current system time is used'))
    parser.add_argument("-l", "--lunch", type=int, nargs='+',
                        help='Update lunch duration for today')
    parser.add_argument("--balance", action='store_true',
                        help='Add a balance day (overtime burnout)')
    parser.add_argument("-t", "--today", action='store_true')
    parser.add_argument("-d", "--debug", action='store_true')

    parser.add_argument("-p", "--period", action='store_true')
    parser.add_argument("-i", "--initdb", action='store_true')
    parser.add_argument("-sd", "--start_date", nargs=1,
                        help='Filter used with the --period command (use now to use today\'s day)')
    parser.add_argument("-ed", "--end_date", nargs=1,
                        help='Filter used with the --period command')

    parser.add_argument("-b", "--backup", action='store_true',
                        help='Backup the database')
    parser.add_argument("-c", "--custom", nargs='*',
                        help=("Call any method from the __Sqlite class."
                              "1st argument is method name anything else "
                              "is passed as arguments to that method"))

    return parser.parse_args()

def main():
    """ main entry point """
    used_args = _get_args()
    if used_args.backup:
        extension = datetime.now().strftime("%Y.%m.%d-%H.%M.%S")
        shutil.copy(SQLITE_FILE, "{}.{}.bck".format(SQLITE_FILE, extension))
    else:
        handle_db_calls(used_args)

if __name__ == "__main__":
    main()

