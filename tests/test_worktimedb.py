import os
import tempfile

import sqlite3

from nose.tools import assert_true, assert_equal

from timekeeper.worktimedb import WorkTimeDB

REF_DB = 'tests/test_db/ref_data.sqlite'

def create_db_instance(db_file):
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    return conn, cursor

def test_db_creation():
    """ Verify that initialize_db method creates a DB with the expected structure """

    new_db_file = tempfile.NamedTemporaryFile(suffix='.sqlite')

    db = WorkTimeDB(sqlite_file=new_db_file.name)
    db.initialize_db()

    # verify that our sqlite file is there
    assert_true(os.path.isfile(new_db_file.name), "DB not created")

    # get the name of the created table (should be only one)
    conn, cursor = create_db_instance(new_db_file.name)
    tables = cursor.execute(
        "SELECT name from SQLITE_MASTER where type='table'").fetchall()


    assert_equal(len(tables), 1, "Got more tables then expected")
    assert_equal(tables[0][0], 'work_days', "Invalid table created")

def test_db_expected_time():
    """ Verify that we get a proper report """
    db = WorkTimeDB(REF_DB)

    assert_equal("Earliest: 17:45", db.expected_time("2016-06-14"),
                "Expected time doesn't match what the test wanted")


