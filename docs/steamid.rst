.. module:: valve.steam.id

SteamIDs
********

SteamID are used in many places within Valve services to identify entities
such as users, groups and game servers. SteamIDs have many different
representations which all need to be handled so the :mod:`valve.steam.id`
module exists to provide an mechanism for representing these IDs in a usable
fashion.

The :class:`SteamID` Class
==========================

Rarely will you ever want to instantiate a :class:`.SteamID` directly. Instead
it is best to use the :meth:`.SteamID.from_community_url` and
:meth:`.SteamID.from_text` class methods for creating new instances.

.. autoclass:: SteamID
    :members:
    :special-members:


Exceptions
==========

.. autoexception:: SteamIDError
    :show-inheritance:


Useful Constants
================

As well as providing the :class:`.SteamID` class, the :mod:`valve.steam.id`
module also contains numerous constants which relate to the contituent parts
of a SteamID. These constants map to their numeric equivalent.


Account Types
-------------
The following are the various account types that can be encoded into a
SteamID. Many of them are seemingly no longer in use -- at least not in
public facing services -- and you're only likely to come across
:data:`TYPE_INDIVIDUAL`, :data:`TYPE_CLAN` and possibly
:data:`TYPE_GAME_SERVER`.

.. autodata:: TYPE_INVALID
.. autodata:: TYPE_INDIVIDUAL
.. autodata:: TYPE_MULTISEAT
.. autodata:: TYPE_GAME_SERVER
.. autodata:: TYPE_ANON_GAME_SERVER
.. autodata:: TYPE_PENDING
.. autodata:: TYPE_CONTENT_SERVER
.. autodata:: TYPE_CLAN
.. autodata:: TYPE_CHAT
.. autodata:: TYPE_P2P_SUPER_SEEDER
.. autodata:: TYPE_ANON_USER


Universes
---------

A SteamID "universe" provides a way of grouping IDs. Typically you'll only
ever come across the :data:`UNIVERSE_INDIVIDUAL` universe.

.. autodata:: UNIVERSE_INDIVIDUAL
.. autodata:: UNIVERSE_PUBLIC
.. autodata:: UNIVERSE_BETA
.. autodata:: UNIVERSE_INTERNAL
.. autodata:: UNIVERSE_DEV
.. autodata:: UNIVERSE_RC
