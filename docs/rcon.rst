.. module:: valve.rcon

Source Remote Console (RCON)
****************************

Source remote console (or RCON) provides a way for server operators to
administer and interact with their servers remotely in the same manner as
the console provided by :program:`srcds`. The :mod:`valve.rcon` module
provides an implementation of the RCON protocol.

RCON is a simple, TCP-based request-response protocol with support for
basic authentication. The RCON client initiates a connection to a server
and  attempts to authenticate by submitting a password. If authentication
succeeds then the client is free to send further requests. These subsequent
requests are interpreted the same way as if you were to type them into
the :program:`srcds` console.

.. warning::
    Passwords and console commands are sent in plain text. Tunneling the
    connection through a secure channel may be advisable where possible.

.. note::
    Multiple RCON authentication failures in a row from a single host will
    result in the Source server automatically banning that IP, preventing
    any subsequent connection attempts.


High-level API
==============

The :mod:`valve.rcon` module provides a number of ways to interact with
RCON servers. The simplest is the :func:`execute` function which executes
a single command on the server and returns the response as a string.

In many cases this may be sufficient but it's important to consider that
:func:`execute` will create a new, temporary connection for every command.
If order to reuse a connection the :class:`RCON` class should be used
directly.

Also note that :func:`execute` only returns Unicode strings which may
prove problematic in some cases. See :ref:`rcon-unicode`.

.. autofunction:: execute


Core API
========

The core API for the RCON implementation is split encapsulated by two
distinct classes: :class:`RCONMessage` and :class:`RCON`.


Representing RCON Messages
--------------------------

Each RCON message, whether a request or a response, is represented by an
instance of the :class:`RCONMessage` class. Each message has three fields:
the message ID, type and contents or body. The message ID of a request is
reflected back to the client when the server returns a response but is
otherwise unsued by this implementation. The type is one of four constants
(represented by three distinct values) which signifies the semantics of the
message's ID and body. The body it self is an opaque string; its value
depends on the type of message.

.. autoclass:: RCONMessage
    :members:
    :exclude-members: Type


.. _rcon-unicode:

Unicode and String Encoding
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The type of the body field of RCON messages is documented as being a
double null-terminated, ASCII-encoded string. At the Python level though
both Unicode strings and raw byte string interfaces are provided by
:attr:`RCONMessage.text` and :attr:`RCONMessage.body` respectively.

In Python you are encouraged to deal with text (a.k.a. Unicode strings)
in preference to raw byte strings unless strictly neccessary. However,
it has been reported that under some conditions RCON servers may return
invalid ASCII sequences in the response body. Therefore it is possible
that the textual representation of the body cannot be determined and
attempts to access :attr:`RCONMessage.text` will fail with a
:exc:`UnicodeDecodeError` being raised.

It appears -- but is not conclusively determined -- that RCON servers in
fact return UTF-8-encoded message bodies, hence why ASCII seems to to work
in most cases. Until this can be categorically proven as the behaviour that
should be expected Python-valve will continue to attempt to process ASCII
strings.

If you come across :exc:`UnicodeDecodeError` whilst accessing response
bodies you will instead have to make-do and handle the raw byte strings
manually. For example:

.. code:: python

    response = rcon.execute("command")
    response_text = response.body.decode("utf-8")

If this is undesirable it is also possible to globally set the encoding
used by :class:`RCONMessage` but this *not* particularly encouraged:

.. code:: python

    import valve.rcon

    valve.rcon.RCONMessage.ENCODING = "utf-8"


Creating RCON Connections
-----------------------------

.. autoclass:: RCON
    :members:
    :special-members: __call__, __enter__, __exit__


Example
^^^^^^^

.. code:: python

    import valve.rcon

    address = ("rcon.example.com", 27015)
    password = "top-secrect-password"
    with valve.rcon.RCON(address, password) as rcon:
        response = rcon.execute("echo Hello, world!")
        print(response.text)


Command-line Client
===================

As well as providing means to programatically interact with RCON servers,
the :mod:`valve.rcon` module also provides an interactive, command-line
client. A client shell can be started by calling :func:`shell` or running
the :mod:`valve.rcon` module.

.. autofunction:: shell


Using the RCON Shell
--------------------

When :func:`shell` is executed, an interactive RCON shell is created. This
shell reads commands from stdin, passes them to a connected RCON server
then prints the response to stdout in a conventional read-eval-print pattern.

By default, commands are treated as plain RCON commmands and are passed
directly to the connected server for evaluation. However, commands prefixed
with an exclamation mark are interpreted by the shell it self:

``!connect``
    Connect to an RCON server. This command accepts two space-separated
    arguments: the address of the server and the corresponding password;
    the latter is optional. If the password is not given the user is
    prompted for it.

    If the shell is already connected to a server then it will disconnect
    first before connecting to the new one.

``!disconnect``
    Disconnect from the current RCON server.

``!shutdown``
    Shutdown the RCON server. This actually just sends an ``exit`` command
    to the server. This must be used instead of ``exit`` as its behaviour
    could prove confusing with ``!exit`` otherwise.

``!exit``
    Exit the shell. This *does not* shutdown the RCON server.

Help is available via the ``help`` command. When connected, an optional
argument can be provided which is the RCON command to show help for.

When connected to a server, command completions are provided via the tab key.


Command-line Invocation
-----------------------

The :mod:`valve.rcon` module is runnable. When ran with no arguments its the
same as calling :func:`shell` with defaults. As with :func:`shell`, the
address and password can be provided as a part of the invoking command:

.. code:: bash

    $ python -m valve.rcon
    $ python -m valve.rcon rcon.example.com:27015
    $ python -m valve.rcon rcon.example.com:27015 --password TOP-SECRET

.. warning::
    Passing sensitive information via command-line arguments, such as
    your RCON password, can be *dangerous*. For example, it can show
    up in :program:`ps` output.


Executing a Single Command
^^^^^^^^^^^^^^^^^^^^^^^^^^

When ran, the module has two modes of execution: the default, which will
spawn an interactive RCON shell and the single command execution mode.
When passed the ``--execute`` argument, :program:`python -m valve.rcon`
will run the given command and exit with a status code of zero upon
completion. The command response is printed to stdout.

This can be useful for simple scripting of RCON commands outside of a
Python environment, such as in a shell script.

.. code:: bash

    $ python -m valve.rcon rcon.example.com:27015 \
        --password TOP-SECRET --execute "echo Hello, world!"


Usage
^^^^^

.. literalinclude:: ../valve/rcon.py
    :pyobject: _USAGE
