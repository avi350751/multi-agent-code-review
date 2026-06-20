"""Example of a flawed sample code for demoing the reviewer.

Contains (at least) one issue per agent domain:
- bug:           mutable default argument + unclosed file handle
- security:      SQL string interpolation + hardcoded credential + eval()
- test_coverage: no tests exist for any of this behaviour
"""

import sqlite3

API_TOKEN = "sk-live-9f8a7b6c5d4e3f2a1b0c"  # security: hardcoded secret


def add_item(item, basket=[]):  # bug: mutable default argument
    basket.append(item)
    return basket


def get_user(db_path, username):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # security: SQL injection via string interpolation
    cur.execute("SELECT * FROM users WHERE name = '%s'" % username)
    return cur.fetchone()  # bug: connection never closed


def load_config(raw):
    return eval(raw)  # security: eval on untrusted input


def read_log(path):
    f = open(path)  # bug: file handle leaked, no context manager
    return f.read()
