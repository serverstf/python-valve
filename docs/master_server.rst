Querying the Source Master Server
*********************************
When a Source server starts it can optionally add it self to an index of
live servers to enable players to find the server via matchmaking and the
in-game server browsers. It does this by registering it self with the "master
server". The master server is hosted by Valve but the protocol used to
communicate with it is *reasonably* well documented.

Clients can request a list of server addresses from the master server for
a particular region. Optionally, they can also specify a filtration criteria
to restrict what servers are returned. :mod:`valve.source.master_server`
provides an interface for interacting with the master server.

.. note::
    Although "master server" is used in a singular context there are in fact
    multiple servers. By default
    :class:`valve.source.master_server.MasterServerQuerier` will lookup
    ``hl2master.steampowered.com`` which, at the time of writing, has three
    ``A`` entries.


valve.source.master_server
==========================

.. automodule:: valve.source.master_server
    :members:
    :special-members:


Example
=======
In this example we will list all European and Asian Team Fortress 2 servers
running the map *ctf_2fort* and print out their addresses.

.. code:: python

    import valve.source.master_server

    msq = valve.source.master_server.MasterServerQuerier()
    for address in msq.find(
            region=["eu", "as"], gamedir="tf", map="ctf_2fort"):
        print "{0}:{1}".format(*address)
