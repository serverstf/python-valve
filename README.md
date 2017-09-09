[![PyPI](https://img.shields.io/pypi/v/python-valve.svg?style=flat-square)](https://pypi.python.org/pypi/python-valve)
[![PyPI](https://img.shields.io/pypi/pyversions/python-valve.svg?style=flat-square)](https://pypi.python.org/pypi/python-valve)
[![Travis](https://img.shields.io/travis/Holiverh/python-valve.svg?style=flat-square)](https://travis-ci.org/Holiverh/python-valve)


# Python-valve #####

Python-valve is a Python library which intends to provide an all-in-one
interface to various Valve products and services, including:

- Source servers
    - A2S server queries
    - RCON
- Source master server
- Steam web API
- Local Steam Clients
- Valve Data Format/KeyValues (.vdf)

To get started, install Python-valve with pip: `pip install python-valve`.


## RCON Example ####

In this example we connect to a Source servers remote console and issue a
simple `echo` command to it.

```python
from valve.source.rcon import RCON

SERVER_ADDRESS = ("...", 27015)
PASSWORD = "top_secret"

with RCON(SERVER_ADDRESS, PASSWORD) as rcon:
    print(rcon("echo Hello, world!"))
```


## Server Query Example ####

In this example we demonstrate the Source master server and A2S query
implementations by listing all Team Fortress 2 servers in Europe
and Asia running the map `ctf_2fort` along with the players on each
server sorted by their score.

```python
import valve.source
import valve.source.a2s
import valve.source.master_server

msq = valve.source.master_server.MasterServerQuerier()
try:
    for address in msq.find(region=[u"eu", u"as"],
                            gamedir=u"tf",
                            map=u"ctf_2fort"):
        server = valve.source.a2s.ServerQuerier(address)
        info = server.info()
        players = server.players()

        print "{player_count}/{max_players} {server_name}".format(**info)
        for player in sorted(players["players"],
                             key=lambda p: p["score"], reverse=True):
            print "{score} {name}".format(**player)
except valve.source.NoResponseError:
    print "Master server request timed out!"
```


## Versioning ####

Python-valve uses [Semantic Versioning](http://semver.org/). At this time,
Python-valve is yet to reach its 1.0 release. Hence, every minor version
should be considered to potentially contain breaking changes. Hence, when
specfiying Python-valve as a requirement, either in `setup.py` or
`requirements.txt` its advised to to pin the specific minor version. E.g.
`python-valve==0.2.0`.


## Testing ####

Python-valve uses [Pytest](https://docs.pytest.org/) for running its test
suite. Unit test coverage is always improving. There are also functional
tests included which run against real Source servers.

If working on Python-valve use the following to install the test
dependencies and run the tests:
```shell
pip install -e .[test]
py.test tests/ --cov valve/
```


## Documentation ####

Documentation is written using [Sphinx](http://www.sphinx-doc.org/) and
is hosted on [Read the Docs](http://python-valve.readthedocs.org/).


## Python 2 ####

Python-valve supports Python 2.7! However, it's important to bare in mind
that Python 2.7 will not be maintained past 2020. As such, Python-valve
*may* drop support for Python 2.7 in future a major release before 2020
in order to make of new, non-backwards compatible Python 3 features.

It's strongly encouraged that new Python-valve projects use Python 3.


## Trademarks ####

Valve, the Valve logo, Half-Life, the Half-Life logo, the Lambda logo,
Steam, the Steam logo, Team Fortress, the Team Fortress logo,
Opposing Force, Day of Defeat, the Day of Defeat logo, Counter-Strike,
the Counter-Strike logo, Source, the Source logo, Counter-Strike:
Condition Zero, Portal, the Portal logo, Dota, the Dota 2 logo, and
Defense of the Ancients are trademarks and/or registered trademarks of
Valve Corporation.

Any reference to these are purely for the purpose of identification.
Valve Corporation is not affiliated with Python-valve or any Python-valve
contributors in any way.
