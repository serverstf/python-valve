Interacting with Source Servers
*******************************
Source provides the "A2S" protocol for querying game servers. This protocol
is used by the Steam and in-game server browsers to list information about
servers such as their name, player count and whether or not they're password
protected. :mod:`valve.source.server` provides a client implementation of
A2S.

.. automodule:: valve.source.a2s
    :members:


Example
=======
In this example we will query a server, printing out it's name and the number
of players currently conected. Then we'll print out all the players sorted
score-decesending.

.. code:: python

    import valve.source.a2s

    SERVER_ADDRESS = (..., ...)

    server = valve.source.a2s.ServerQuerier(SERVER_ADDRESS)
    info = server.info()
    players = server.players()

    print "{player_count}/{max_players} {server_name}".format(**info)
    for player in sorted(players["players"],
                         key=lambda p: p["score"], reverse=True):
        print "{score} {name}".format(**player)


Utilities
=========
:mod:`valve.source.util` provides a handful of utility classes which are
used when querying Source servers.

.. automodule:: valve.source.util
    :members:
    :special-members:
