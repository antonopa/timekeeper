"""
Wrapper class to handle sqlite3 DB and offer helper methods to handle operations around the
overtime data
"""
import sqlite3
from datetime import datetime, timedelta
from pprint import PrettyPrinter


class DBOperationError(Exception):
    """ Basic exception to communicate DB operation fails """
    pass

def _sec2humantime(secs):
    """ Convert to human readable time """
    return str(timedelta(seconds=secs))

def _get_isotime(time):
    return datetime.now().strftime("%H:%M:%S") if time is 'now' else time

class __Sqlite:
    __sqlite_file = '/home/antonopa/.timekeeper.sqlite'

    def __init__(self, sqlite_file=__sqlite_file):
        self.sqlite_file = sqlite_file
        self._debug = False
        self.table = 'work_days'
        self.prettyprint = PrettyPrinter(indent=2).pprint
        self.conn = sqlite3.connect(sqlite_file)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    @property
    def debug(self):
        """ Enable or disable debug output in different class methods """
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = value

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.conn.close()

    def initialize_db(self, table=None):
        """ initialize a database """
        db_table = table if table else self.table
        table_cmd = ("CREATE TABLE {_t} "
                     "(day text, srart text, end text, vacation int, "
                     "lunch_duration int, unique(day))")
        self.cursor.execute(table_cmd.format(_t=db_table))

        create_index = "CREATE UNIQUE INDEX date_idx ON {_t} (day)"
        self.cursor.execute(create_index.format(_t=db_table))

        self.conn.commit()

    def insert_day(self, day='now', end=None, lunch_duration=45):
        """ Insert a new entry (aka work day) """
        if not end:
            end = (datetime.now() + timedelta(hours=8, minutes=45)).strftime("%H:%M:%S")
        start = datetime.now().strftime("%H:%M:%S")
        _query = "INSERT INTO {table} VALUES(DATE('{_d}'), TIME('{_s}'), TIME('{_e}'), 0, {_l});"
        if self.debug:
            print(_query.format(table=self.table, _d=day, _s=start, _e=end, _l=lunch_duration))
        try:
            self.cursor.execute(
                _query.format(table=self.table, _d=day, _s=start, _e=end, _l=lunch_duration))
            self.conn.commit()
        except sqlite3.IntegrityError:
            print("Day already exists")

    def update_start(self, day='now', time='now'):
        """ Update the start time for a given day """
        _query = "UPDATE {_table} SET start=TIME('{_s}') WHERE day=DATE('{_d}')"
        self.cursor.execute(_query.format(_table=self.table, _d=day, _s=_get_isotime(time)))
        self.conn.commit()

    def update_end(self, day='now', end='now'):
        """ Update the time a work day is finished. Default is today and time is
        the current system time """
        _query = "UPDATE {_table} SET end=TIME('{_e}') WHERE day=DATE('{_d}')"
        self.cursor.execute(_query.format(_table=self.table, _d=day, _e=_get_isotime(end)))
        self.conn.commit()

    def update_lunch(self, lunch_time, day='now'):
        """ Update the duration of lunch. if 'day' is not specified today is used """
        _query = "UPDATE {_table} SET lunch_duration={_lt} WHERE day=DATE('{_day}')"
        self.cursor.execute(_query.format(_table=self.table, _day=day, _lt=lunch_time))
        self.conn.commit()

    def convert_vacation(self, day='now', vacation=None):
        """ Toggle vacation flag for a day or set it explicitly to the input argument"""
        query = self._create_query(start_date=day, end_date=day, with_vacation=True)
        res = self._parse_results(self.cursor.execute(query))

        if self._debug:
            self.prettyprint(res)

        # We only want to change an existing day. sqlite3 UPDATE fails silently if day
        # isn't found and this way we can raise an exception.
        if res:
            if vacation is not None:
                vflag = vacation
            else:
                today = datetime.now().strftime("%Y-%m-%d")
                vflag = not res[today]['vacation']
            update = "UPDATE {_t} SET vacation={_v} WHERE day=DATE('{_d}')".format(
                _t=self.table, _v=int(vflag), _d=day)
            if self._debug:
                self.prettyprint(update)

            self.cursor.execute(update)
            self.conn.commit()
        else:
            day = datetime.now().strftime("%Y-%m-%d") if day == 'now' else day
            raise DBOperationError("Day {} doesn't exist".format(day))

    def expected_time(self, day='now'):
        """ Calculate the expected time to leave the office taking into account the starting time
        for the provided day """
        query = ("SELECT day,start,lunch_duration FROM work_days "
                 "WHERE vacation!=1 AND day=DATE('{_d}')")
        rows = self.cursor.execute(query.format(_d=day))
        res = rows.fetchall()[0]
        start = datetime.strptime(res['start'], "%H:%M:%S")
        end = start + timedelta(hours=8, minutes=res['lunch_duration'])

        return "Earliest: {_h}:{_m}".format(_h=end.hour, _m=end.minute)

    def _parse_results(self, sql_rows):
        """ Parse DB results and convert them to a python dictionary """
        res = {}
        for row in sql_rows.fetchall():
            data = dict(row)
            if self._debug:
                self.prettyprint(data)
            data['diff_human'] = _sec2humantime(row['diff_sec'])
            res[data['day']] = data
            data.pop('day')

        return res

    def _create_query(self, start_date=None, end_date=None, with_vacation=False):
        """ Build a query to collect all data from the DB

        Args:
            start_date(str): return only results after this day; default is from 1st day in DB
            end_date(str): return only results up to this day; default is up to last day in DB
            with_vacation(bool): include vacation days in the results
        """
        vacation_check = "" if with_vacation else "vacation!=1"
        query = ("SELECT day,start,end,lunch_duration,vacation,"
                 "((strftime('%s', end)-strftime('%s', start))/60 + 45 - lunch_duration) "
                 "AS diff_sec FROM work_days WHERE {_vacation} {_period} ORDER BY day")

        period = ""
        if start_date and end_date:
            period = "day>=DATE('{}') AND day<=DATE('{}')".format(start_date, end_date)
        elif start_date:
            period = "day>=DATE('{}')".format(start_date)
        elif end_date:
            period = "day<=DATE('{}')".format(end_date)

        if period and not with_vacation:
            period = "AND {}".format(period)

        query = query.format(_vacation=vacation_check, _period=period)
        if self._debug:
            print(query)

        return query

    def get_period(self, start_date=None, end_date=None, with_vacation=False):
        """ Retrieve DB Entries for a specific period

        args:
            start_date(str): start of period; defaults to first entry in DB if nothing is provided
            end_date(str): end of period; defaults to last entry in DB if nothing is provided
            with_vacation(bool): flag to include or exclude vacation
        """
        return self._parse_results(
            self.cursor.execute(self._create_query(start_date, end_date, with_vacation)))

    def get_all(self):
        """ Retrieve all date from the DB """
        return self.get_period()

    def get_overtime(self, start_date=None, end_date=None):
        """ Calculate the overtime over a specific period """
        full_day = 480 + 45

        rows = self.cursor.execute(self._create_query(start_date, end_date))

        res = []
        for row in rows.fetchall():
            overtime = row['diff_sec'] - full_day
            res.append((row['day'], overtime, _sec2humantime(abs(overtime))))
        return res

    def overtime_to_str(self, start_date=None, end_date=None):
        """ Convert overtime over a period to a human readable format """
        time_diff = sum([x[1] for x in self.get_overtime(start_date, end_date)])
        return "{} time: {}".format(
            "Excess" if time_diff > 0 else "Due",
            str(timedelta(seconds=abs(time_diff))))

    def add_vacation(self, start_date=None):
        """ Insert a new day in the DB and mark it as vacation day """
        query = "INSERT INTO {_t} VALUES(DATE('{_d}'), TIME('00:00:00'), TIME('00:00:00'), 1, 0);"
        if start_date is None:
            start_date = 'now'
        self.cursor.execute(query.format(_d=start_date, _t=self.table))
        self.conn.commit()

    def per_day(self):
        """ Convert DB output to a short per day summary """
        return ["day %s -> %s" % (x[0], x[1]['diff_human']) for x in sorted(self.get_all().items())]
