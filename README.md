python-valve
============

`python-valve` is a Python library which intends to provide an all-in-one
interface to various Valve products and services, including:

- Steam web API
- Local Steam Clients
- Source servers
    - A2S server queries
    - RCON
- Source master server
- Valve Data Format (.vdf) (de)serialiser

Example
--------
In this example we demonstrate the Source master server and A2S query
implementations by listing all Team Fortress 2 servers in Europe
and Asia running the map `ctf_2fort` along with the players on each
server sorted by their score.

```
import valve.source.server
import valve.source.master_server

msq = valve.source.master_server.MasterServerQuerier()
try:
    for address in msq.find(region=["eu", "as"],
                            gamedir="tf",
                            map="ctf_2fort"):
        server = valve.source.server.ServerQuerier(address)
        try:
            info = server.get_info()
            players = server.get_players()
        except valve.source.server.NoResponseError:
            continue
        print "{player_count}/{max_players} {server_name}".format(**info)
        for player in sorted(players["players"],
                             key=lambda p: p["score"], reverse=True):
            print "  {score} {name}".format(**player)
except valve.source.server.NoResponseError:
    print "Master server request timed out!"
```

Testing
-------
`python-valve` uses `py.test` for running its test suite as well as using
Jenkins CI to actively test the A2S implementation against thousands of
servers.  See http://servers.tf:8080/.

Documentation
-------------
Documentation is hosted on read the docs at
http://python-valve.readthedocs.org/.

Python 3
--------
Currently there is partial support for Python 3 -- 3.4 to be specific.
Everything in `valve.source` will/should work in both Python 2.7 and
Python 3.4 but currently that is the only section that has been ported. The
rest will be updated in due course but those other components need reworking
anyway.
