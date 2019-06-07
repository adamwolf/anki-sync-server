=============
``ankisyncd``
=============

.. image:: https://img.shields.io/circleci/build/gh/adamwolf/anki-sync-server.svg
    :target: https://circleci.com/gh/adamwolf/anki-sync-server
    :alt: CI status including tests and code style

```ankisyncd``` is an open-source sync server for Anki.

`Anki <https://apps.ankiweb.net/>`_  is a powerful flashcard program. The desktop application, for Windows, macOS, and
Linux, is open source. The Android version, AnkiDroid, is also open source.  AnkiWeb, which provides both a web-based user interface and syncing for the other platforms, is no cost but closed source.

Installation
============

0. Install Anki. The currently supported version range is 2.1.1〜2.1.11, with the
   exception of 2.1.9. (Keep in mind this range only applies to the Anki used by
   the server, clients can be as old as 2.0.27 and still work.) Running the server
   with other versions might work as long as they're not 2.0.x, but things might
   break, so do it at your own risk. If for some reason you can't get the supported
   Anki version easily on your system, you can use `anki-bundled` from this repo:

        ``$ git submodule update --init``

        ``$ pip install -r anki-bundled/requirements.txt``

   Keep in mind `pyaudio`, a dependency of Anki, requires development headers for
   Python 3 and PortAudio to be present before running `pip`. If you can't or
   don't want to install these, you don't have to.  If you are running Anki ≥2.1.9,
   just remove pyaudio from anki-bundled/requirements.txt and run ``pip install -r anki-bundled/requirements.txt``.  If you are running an
   older version of Anki, see `Running ankisyncd without pyaudio`_.

1. Install the dependencies:

        ``$ pip install -r requirements.txt``

2. Modify ankisyncd.conf according to your needs.

3. Create user:

        ``$ ./ankisyncctl.py adduser <username>``

4. Run ankisyncd in development mode:

       ``$ FLASK_APP="ankisyncd" flask run``

Developing
==========

You can run all the tests and style checks by running ``tox``.

If you want to develop, you'll probably want a virtualenv.  You can install ``requirements.txt``, ``test-requirements.txt``, and ``dev-requirements.txt``.

We've set up pre-commit, which does some code formatting things before you commit.  You can set it up by running ``pre-commit run --all-files``.

If you're using an IDE, you may need to add anki-bundled to your ``PYTHONPATH``. 
In PyCharm, this can be done under Preferences, Interpreter, Configure, Show Paths, Add.


Usage
=====

Once ankisyncd has been installed, it can be run using the Flask development server with

        ``$ FLASK_APP="ankisyncd" flask run``

There are `a lot of ways <http://flask.pocoo.org/docs/1.0/deploying/>`_ to deploy Flask in production.

Setting up the Anki client
--------------------------

On Anki Desktop, use the `SyncRedirector <https://ankiweb.net/shared/info/2124817646>_` plugin .

On AnkiDroid, go into Settings, Advanced, Custom Sync Server.  Don't use trailing slashes.  When AnkiDroid asks for an email address, you can use the username you set up in ``ankisyncd`` even if it does not look like an email address.

Security
========

If you use HTTP, all the data, including the password, is sent unencrypted.  Do not deploy this in production without using HTTPS!

Getting Help
============

Please `file an issue <https://github.com/adamwolf/anki-sync-server/issues>`_ on GitHub.

Project Information
===================

```ankisyncd``` is released under the
`GNU Affero General Public License v3.0 <https://choosealicense.com/licenses/agpl-3.0/>`_ license.

The code is on `GitHub <https://github.com/adamwolf/anki-sync-server>`_.

It’s tested on Python 3.

If you'd like to contribute to ```ankisyncd``` you're most welcome.   Take a look at the issues for ideas or submit a PR!

History
=======

I have done my best to document the history, but please let me know if I need to make adjustments!

```ankisyncd``` was written by `dsnopek <https://github.com/dsnopek>_` `here <https://github.com/dsnopek/anki-sync-server>_`.

`jdoe3 <https://github.com/jdoe0/ankisyncd>_` removed the REST API to remove some dependencies, and then `tsudoko <https://github.com/tsudoko/anki-sync-server>_` added support for Python 3 and Anki 2.1.

This version, so far, is primarily by Adam Wolf.  It moves from webob to Flask.  It adds a bunch of python tooling, like tox and adds continuous integration.



Running `ankisyncd` without `pyaudio`
-------------------------------------

`ankisyncd` doesn't use the audio recording feature of Anki, so if you don't
want to install PortAudio, you can edit some files in the `anki-bundled`
directory to exclude `pyaudio`.

Anki ≥2.1.9
^^^^^^^^^^^

    Just remove "pyaudio" from requirements.txt and you're done.

Older versions
^^^^^^^^^^^^^^

    First go to `anki-bundled`, then follow one of the instructions below. They all
    do the same thing, you can pick whichever one you're most comfortable with.

    Manual version:
           
        remove every line after "# Packaged commands" in anki/sound.py, and remove every line starting with "pyaudio" in requirements.txt

    ``ed`` version:

        ``$ echo '/# Packaged commands/,$d;w' | tr ';' '\n' | ed anki/sound.py``

        ``$ echo '/^pyaudio/d;w' | tr ';' '\n' | ed requirements.txt``

    ``sed -i`` version:

        ``$ sed -i '/# Packaged commands/,$d' anki/sound.py``

        ``$ sed -i '/^pyaudio/d' requirements.txt``


Environment variable configuration overrides
--------------------------------------------

Configuration values can be set via environment variables using `ANKISYNCD_` prepended
to the uppercase form of the configuration value. E.g. the environment variable,
`ANKISYNCD_AUTH_DB_PATH` will set the configuration value `auth_db_path`

Environment variables override the values set in the `ankisyncd.conf`.

Support for other database backends
-----------------------------------

sqlite3 is used by default for user data, authentication and session persistence.

`ankisyncd` supports loading classes defined via config that manage most
persistence requirements (the media DB and files are being worked on). All that is
required is to extend one of the existing manager classes and then reference those
classes in the config file. See ankisyncd.conf for the example config.
