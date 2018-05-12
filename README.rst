API
======

Sample API with Flask and Python


Install
-------

Create a virtualenv and activate it::

    python3 -m venv venv
    . venv/bin/activate

Or on Windows cmd::

    py -3 -m venv venv
    venv\Scripts\activate.bat

Install Application::

    pip install -e .


Setup mongodb:

    setup mongo database url, test and dev databases
    in app/dev.cfg and app/test.cfg

Run
---

::

    export FLASK_APP=app
    export FLASK_ENV=development
    flask run

Or on Windows cmd::

    set FLASK_APP=app
    set FLASK_ENV=development
    flask run

Open http://127.0.0.1:5000/setup/test/data in a browser. This will populate the dev database with some data.

After that, you can start using the API.


    http://127.0.0.1:5000/songs/<page_size>/<page_num>
    http://127.0.0.1:5000/songs/avg/difficulty/<level>
    http://127.0.0.1:5000/songs/avg/rating/<song_id>
    http://127.0.0.1:5000/songs/search/<message>

or

   curl http://localhost:5000/songs/10/2 -X GET -v
	
or
	
   curl http://localhost:5000/songs/rating -d '{"song_id":"5af52fb1b8dd0d53888e9f7d", "rating": 3}' -X POST -v


Test
----

::
    pip install pytest
    pytest

