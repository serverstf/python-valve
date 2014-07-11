.. module:: valve.source.rcon


Source Remote Console (RCON)
****************************

The remote console (RCON) is available in all Source Dedicated Servers and
it provides a way for server operators to access and administer their servers
remotely. The :mod:`valve.source.rcon` module provides an implementation of
the RCON protocol.

RCON is a request-response TCP based protocol with a simple authentication
mechanism. The client initiates a connection with the server and attempts to
authenticate by submitting a password. If authentication suceeds then the
client is free to send further requests to the server in the same manner
as you may do using the Source in-game console.

.. warning::

    RCON does not use secure transport so the password is sent as plain text.

.. note::

    Many RCON authentication failures in a row from a single host will result
    in the Source server automatically banning that IP, preventing any
    subsequent connection attempts.


Example
=======

.. code:: python

    from valve.source.rcon import RCON

    SERVER_ADDRESS = ("...", 27015)
    PASSWORD = "top_secret"

    with RCON(SERVER_ADDRESS, PASSWORD) as rcon:
        print(rcon("echo Hello, world!"))

In this example a :class:`RCON` instance is created to connect to a Source
RCON server, authenticating using the given password. Then the ``echo`` RCON
command is issued which simply prints out what it receives.

Using the :class:`RCON` object with the ``with`` statement means creation and
clean up of the underlying TCP socket will happen automatically. Also, if the
password is specified, the client will authenticate immediately after
connecting.


The :class:`RCON` Class
=======================

The :class:`RCON` class implements the RCON client protocol. It supports the
ability to finely grain transport creation, connection, authentication and
clean up although its encouraged to make use of the ``with`` statement as
shown in the example above.

.. autoclass:: RCON
    :members:
    :special-members:


RCON Messages
=============

RCON *requests* and *responses* are generalised as *messages* in the
python-valve implementation. If you're using :meth:`RCON.__call__` then you
won't need to worry about handling individual messages. However,
:meth:`RCON.execute` returns these raw messages so their structure is
documented below.

.. autoclass:: Message
    :members:
    :special-members:


REPL via :func:`shell`
======================

A small convenience function is provided by the :mod:`valve.source.rcon`
module for creating command-line REPL interfaces for RCON connections.

.. autofunction:: shell