|PyPI| |PyPIPythonVersions| |Travis| |Coveralls|

Python-valve
============

Python-valve is a Python library which intends to provide an all-in-one
interface to various Valve products and services, including:

-  Source servers

   -  A2S server queries
   -  RCON

-  Source master server
-  Steam web API
-  Local Steam Clients
-  Valve Data Format/KeyValues (.vdf)

To get started, install Python-valve with pip:
``pip install python-valve``.

UNMAINTAINED
------------

This project is no longer actively maintained. The server query part
has been rewritten and is available as
`python-a2s <https://github.com/Yepoleb/python-a2s>`__ to not break
compatibility with projects using the old API.

RCON Example
------------

In this example we connect to a Source server's remote console and issue
a simple ``echo`` command to it.

.. code:: python

    import valve.rcon

    server_address = ("...", 27015)
    password = "top_secret"

    with valve.rcon.RCON(server_address, password) as rcon:
        print(rcon("echo Hello, world!"))


Server Query Example
--------------------

In this example we demonstrate the Source master server and A2S query
implementations by listing all Team Fortress 2 servers in Europe and
Asia running the map ``ctf_2fort``, along with the players on each server
sorted by their score.

.. code:: python

    import valve.source
    import valve.source.a2s
    import valve.source.master_server

    with valve.source.master_server.MasterServerQuerier() as msq:
        try:
            for address in msq.find(region=[u"eu", u"as"],
                                    gamedir=u"tf",
                                    map=u"ctf_2fort"):
                try:
                    with valve.source.a2s.ServerQuerier(address) as server:
                        info = server.info()
                        players = server.players()

                except valve.source.NoResponseError:
                    print("Server {}:{} timed out!".format(*address))
                    continue

                print("{player_count}/{max_players} {server_name}".format(**info))
                for player in sorted(players["players"],
                                     key=lambda p: p["score"], reverse=True):
                    print("{score} {name}".format(**player))

        except valve.source.NoResponseError:
            print("Master server request timed out!")



Versioning
----------

Python-valve uses `Semantic Versioning <http://semver.org/>`__. At this
time, Python-valve is yet to reach its 1.0 release. Hence, every minor
version should be considered to potentially contain breaking changes.
Hence, when specifying Python-valve as a requirement, either in
``setup.py`` or ``requirements.txt``, it's advised to to pin the
specific minor version. E.g. ``python-valve==0.2.0``.


Testing
-------

Python-valve uses `Pytest <https://docs.pytest.org/>`__ for running its
test suite. Unit test coverage is always improving. There are also
functional tests included which run against real Source servers.

If working on Python-valve use the following to install the test
dependencies and run the tests:

.. code:: shell

    pip install -e .[test]
    py.test tests/ --cov valve/


Documentation
-------------

Documentation is written using `Sphinx <http://www.sphinx-doc.org/>`__
and is hosted on `Read the Docs <http://python-valve.readthedocs.org/>`__.

If working on Python-valve use the following to install the documentation
dependencies, build the docs and then open them in a browser.

.. code:: shell

    pip install -e .[docs]
    (cd docs/ && make html)
    xdg-open docs/_build/html/index.html


Python 2
--------

Python-valve supports Python 2.7! However, it's important to bear in
mind that Python 2.7 will not be maintained past 2020. Python-valve
*may* drop support for Python 2.7 in a future major release before 2020
in order to make use of new, non-backwards compatible Python 3 features.

It's strongly encouraged that new Python-valve projects use Python 3.


Trademarks
----------

Valve, the Valve logo, Half-Life, the Half-Life logo, the Lambda logo,
Steam, the Steam logo, Team Fortress, the Team Fortress logo, Opposing
Force, Day of Defeat, the Day of Defeat logo, Counter-Strike, the
Counter-Strike logo, Source, the Source logo, Counter-Strike: Condition
Zero, Portal, the Portal logo, Dota, the Dota 2 logo, and Defense of the
Ancients are trademarks and/or registered trademarks of Valve
Corporation.

Any reference to these are purely for the purpose of identification.
Valve Corporation is not affiliated with Python-valve or any
Python-valve contributors in any way.

.. |PyPI| image:: https://img.shields.io/pypi/v/python-valve.svg?style=flat-square
   :target: https://pypi.python.org/pypi/python-valve
.. |PyPIPythonVersions| image:: https://img.shields.io/pypi/pyversions/python-valve.svg?style=flat-square
  :target: https://pypi.python.org/pypi/python-valve
.. |Travis| image:: https://img.shields.io/travis/serverstf/python-valve.svg?style=flat-square
   :target: https://travis-ci.org/serverstf/python-valve
.. |Coveralls| image:: https://img.shields.io/coveralls/serverstf/python-valve.svg?style=flat-square
   :target: https://coveralls.io/github/serverstf/python-valve
