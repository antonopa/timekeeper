import sqlite3
from datetime import datetime, timedelta
from pprint import PrettyPrinter


def _sec2humantime(secs):
    """ Convert to human readable time """
    return str(timedelta(seconds=secs))

def _get_isotime(time):
    return datetime.now().strftime("%H:%M:%S") if time is 'now' else time

class __Sqlite:
    __sqlite_file = '/home/antonopa/.timekeeper.sqlite'

    def __init__(self, sqlite_file = __sqlite_file):
        self.sqlite_file = sqlite_file
        self._debug = False
        self.table = 'work_days'
        self.prettyprint = PrettyPrinter(indent=2).pprint
        self.conn = sqlite3.connect(sqlite_file)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = value

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        if type is not None:
            pass
        self.conn.close()

    def initialize_db(self, table = None):
        """ initialize a database """
        db_table = table if table else self.table
        table_cmd = ("CREATE TABLE {_t} "
                     "(day text, start text, end text, vacation int, lunch_duration int, unique(day))")
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
            self.cursor.execute(_query.format(table=self.table, _d=day, _s=start, _e=end, _l=lunch_duration))
            self.conn.commit()
        except sqlite3.IntegrityError:
            print("Day already exists")

    def update_start(self, day='now', time='now'):
        _query = "UPDATE {_table} SET start=TIME('{_s}') WHERE day=DATE('{_d}')"
        self.cursor.execute(_query.format(_table=self.table, _d=day, _s=__Sqlite._get_isotime(time)))
        self.conn.commit()

    def update_end(self, day='now', end='now'):
        """ Update the time a work day is finished. Default is today and time is the current system time """
        _query = "UPDATE {_table} SET end=TIME('{_e}') WHERE day=DATE('{_d}')"
        self.cursor.execute(_query.format(_table=self.table, _d=day, _e=_get_isotime(end)))
        self.conn.commit()

    def update_lunch(self, lunch_time, day='now'):
        """ Update the duration of lunch. if 'day' is not specified today is used """
        _query = "UPDATE {_table} SET lunch_duration={_lt} WHERE day=DATE('{_day}')"
        self.cursor.execute(_query.format(_table=self.table, _day=day, _lt=lunch_time))
        self.conn.commit()

    def expected_time(self, day='now'):
        query = "SELECT day,start,lunch_duration from work_days where vacation!=1 and day=DATE('{_d}')"
        c = self.cursor.execute(query.format(_d = day))
        res = c.fetchall()[0]
        start = datetime.strptime(res['start'], "%H:%M:%S")
        end = start + timedelta(hours=8, minutes=res['lunch_duration'])

        return "Earliest: {_h}:{_m}".format(_h = end.hour, _m = end.minute)

    def _parse_results(self, sql_rows):
        res = {}
        for row in sql_rows.fetchall():
            _d = dict(row)
            _d['diff_human'] = _sec2humantime(row['diff_sec'])
            res[ _d['day'] ] = _d
            _d.pop('day')

        return res

    def _create_query(self, start_date=None, end_date=None, with_vacation=False):
        """ Build a query to collect all data from the DB

        Args:
            start_date(str): return only results after this day; default is from 1st day in DB
            end_date(str): return only results up to this day; default is up to last day in DB
            with_vacation(bool): include vacation days in the results
        """
        vacation_check = "" if with_vacation else "vacation!=1"
        query = ("SELECT day,start,end,lunch_duration,"
                  "((strftime('%s', end)-strftime('%s', start))/60 + 45 - lunch_duration) AS diff_sec "
                  "FROM work_days WHERE {_vacation} {_period} ORDER BY day")

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
        return self._parse_results(self.cursor.execute(self._create_query(start_date, end_date, with_vacation)))


    def get_all(self):
        return self.get_period()

    def get_overtime(self, start_date=None, end_date=None):
        full_day = 480 + 45

        c = self.cursor.execute(self._create_query(start_date, end_date))

        res = []
        for row in c.fetchall():
            overtime = row['diff_sec'] - full_day
            res.append( (row['day'], overtime, _sec2humantime(abs(overtime))) )
        return res

    def overtime_to_str(self, start_date=None, end_date=None):
        time_diff = sum([ x[1] for x in self.get_overtime(start_date, end_date) ])
        return "{} time: {}".format(
                "Excess" if time_diff > 0 else "Due",
                str(timedelta(seconds = abs(time_diff)))
                )

    def add_vacation(self, start_date = None, end_date = None):
        _query = "INSERT INTO {table} VALUES(DATE('{_d}'), TIME('00:00:00'), TIME('00:00:00'), 1, 0);"
        if not start_date:
            start_date = 'now'
        self.cursor.execute(_query.format(_d = start_date, table=self.table))
        self.conn.commit()

    def per_day(self):
        return [ "day %s -> %s" % (x[0], x[1]['diff_human']) for x in sorted(self.get_all().items()) ]
