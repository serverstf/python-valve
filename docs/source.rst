Interacting with Source Servers
*******************************

.. module:: valve.source.a2s

Source provides the "A2S" protocol for querying game servers. This protocol
is used by the Steam and in-game server browsers to list information about
servers such as their name, player count and whether or not they're password
protected. :mod:`valve.source.a2s` provides a client implementation of
A2S.

.. autoclass:: valve.source.a2s.ServerQuerier
    :members:


Example
=======
In this example we will query a server, printing out it's name and the number
of players currently conected. Then we'll print out all the players sorted
score-decesending.

.. code:: python

    import valve.source.a2s

    SERVER_ADDRESS = (..., ...)

    with valve.source.a2s.ServerQuerier(SERVER_ADDRESS) as server:
        info = server.info()
        players = server.players()

    print("{player_count}/{max_players} {server_name}".format(**info))
    for player in sorted(players["players"],
                         key=lambda p: p["score"], reverse=True):
        print("{score} {name}".format(**player))


Queriers and Exceptions
=======================

.. module:: valve.source

Both :class:`valve.source.a2s.ServerQuerier` and
:class:`valve.source.master_server.MasterServerQuerier` are based on a
common querier interface. They also raise similar exceptions. All of these
live in the :mod:`valve.source` module.

.. autoclass:: valve.source.BaseQuerier
    :members:

.. autoexception:: valve.source.NoResponseError

.. autoexception:: valve.source.QuerierClosedError


Identifying Server Platforms
============================

.. module:: valve.source.util

:mod:`valve.source.util` provides a handful of utility classes which are
used when querying Source servers.

.. automodule:: valve.source.util
    :members:
    :special-members:
