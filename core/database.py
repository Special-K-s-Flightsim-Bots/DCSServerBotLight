import sqlite3
from contextlib import contextmanager


@contextmanager
def DBConnection():
    conn = sqlite3.connect("dcsserverbot.db")
    conn.row_factory = sqlite3.Row
    try:
        yield conn.cursor()
        conn.commit()
    except sqlite3.Error as ex:
        print(ex)
        conn.rollback()
    finally:
        conn.close()
