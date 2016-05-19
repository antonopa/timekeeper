#!/usr/bin/env python3
from timekeeper import db
import argparse
import pprint
from datetime import datetime
import shutil


__sqlite_file = '/home/antonopa/.timekeeper.sqlite'

def call_retriever(func):
    """ Harvest input argument for reporting period and call the desired
        function """
    start = args.start_date[0] if args.start_date else None
    end = args.end_date[0] if args.end_date else None
    return func(start, end)

def handle_db_calls(args):
    """ Handle all db related calls here """

    myp = pprint.PrettyPrinter(indent=2).pprint

    with db.__Sqlite(__sqlite_file) as tk:
        if args.debug:
            tk.debug = True
        if args.add:
            tk.insert_day(args.add[0])
        if args.balance:
            print(args.balance)
            tk.insert_day(day='now' if not args.start_date else args.start_date[0],
                    end=datetime.now().strftime("%H:%M:%S"),
                    lunch_duration=0)

        if args.out:
            print(tk.expected_time())
        if args.show:
            if args.show >= 1:
                print("Overtime sum: ")
                myp(call_retriever(tk.overtime_to_str))
            if args.show >= 2:
                print("\nOvertime per day: ")
                myp(call_retriever(tk.get_overtime))
            if args.show >= 3:
                print("\nEverything: ")
                myp(call_retriever(tk.get_period))

        if args.update is not None:
            end = args.update[0] if args.update else 'now'
            tk.update_end(day='now', end=end)
        if args.period:
            start = args.start_date[0] if args.start_date else None
            end = args.end_date[0] if args.end_date else None
            myp(tk.get_period(start, end))
        if args.lunch:
            tk.update_lunch(args.lunch[0])
        if args.custom:
            """ first argument is the method call. We pass everything else as arguments to that method """
            method = getattr(tk, args.custom[0], None)
            args = args.custom[1:]
            print(args)
            if callable(method):
                myp(method(*args))

def _get_args():
    """ Add all the needed arguments in ArgumentParser and return the ones with which this was called """
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--add", nargs='*',
            help='Add new day in the DB')
    parser.add_argument("-o", "--out", action='store_true',
            help='Print the end of the current work day')
    parser.add_argument("-s", "--show", action='count',
            help='Print report. Repeat the option for more info')
    parser.add_argument("-u", "--update", nargs='*',
            help='Update end of today\'s work day. Optionally provide time else current system time is used')
    parser.add_argument("-l", "--lunch", type=int, nargs='+',
            help='Update lunch duration for today')
    parser.add_argument("--balance", action='store_true',
            help='Add a balance day (overtime burnout)')
    parser.add_argument("-t", "--today", action='store_true')
    parser.add_argument("-d", "--debug", action='store_true')

    parser.add_argument("-p", "--period", action='store_true')
    parser.add_argument("-sd", "--start_date", nargs=1,
            help='Filter used with the --period command (use now to use today\'s day)')
    parser.add_argument("-ed", "--end_date", nargs=1,
            help='Filter used with the --period command')

    parser.add_argument("-b", "--backup", action='store_true',
            help='Backup the database')
    parser.add_argument("-c", "--custom", nargs='*',
            help=("Call any method from the __Sqlite class."
                  "1st argument is method name anything else "
                  "is passed as arguments to that method")
            )

    return parser.parse_args()

if __name__ == "__main__":
    args = _get_args()
    if args.backup:
        extension = datetime.now().strftime("%Y.%m.%d-%H.%M.%S")
        shutil.copy(__sqlite_file, "{}.{}.bck".format(__sqlite_file, extension))
    else:
        handle_db_calls(args)

