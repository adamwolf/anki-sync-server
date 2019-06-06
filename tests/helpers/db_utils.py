# -*- coding: utf-8 -*-
import sqlite3


def from_sql(path, sql):
    """
    Creates an SQLite db and executes the passed sql statements on it.

    :param path: the path to the created db file
    :param sql: the sql statements to execute on the newly created db
    """

    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.executescript(sql)
    connection.commit()
    connection.close()


def to_sql(database):
    """
    Returns a string containing the sql export of the database. Used for
    debugging.

    :param database: either the path to the SQLite db file or an open
                     connection to it
    :return: a string representing the sql export of the database
    """

    if type(database) == str:
        connection = sqlite3.connect(database)
    else:
        connection = database

    res = '\n'.join(connection.iterdump())

    if type(database) == str:
        connection.close()

    return res


def diff(left_db_path, right_db_path):
    """
    Compare two sqlite files for equality.
    Returns True if the databases differ, False if they don't.

    :param left_db_path: path to the left db file
    :param right_db_path: path to the right db file
    :return: True if the specified databases differ, False else
    """

    left = to_sql(left_db_path)
    right = to_sql(right_db_path)

    # import difflib
    # d = difflib.Differ()
    # diff = d.compare(left.split("\n"), right.split("\n"))
    # print('\n'.join(diff))

    return left != right
