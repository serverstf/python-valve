# -*- coding: utf-8 -*-
# Copyright (C) 2013-2017 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import monotonic

import valve.source
from . import messages


# NOTE: backwards compatability; remove soon(tm)
NoResponseError = valve.source.NoResponseError


class ServerQuerier(valve.source.BaseQuerier):
    """Implements the A2S Source server query protocol.

    https://developer.valvesoftware.com/wiki/Server_queries

    .. note::
        Instantiating this class creates a socket. Be sure to close the
        querier once finished with it. See :class:`valve.source.BaseQuerier`.
    """

    def request(self, request):
        super(ServerQuerier, self).request(
            messages.Header(split=messages.NO_SPLIT), request)

    def get_response(self):

        data = valve.source.BaseQuerier.get_response(self)

        # According to https://developer.valvesoftware.com/wiki/Server_queries
        # "TF2 currently does not split replies, expect A2S_PLAYER and
        # A2S_RULES to be simply cut off after 1260 bytes."
        #
        # However whilst testing info() on a TF2 server, it did
        # set the split header to -2. So it is unclear whether the
        # warning means that only one fragment of the message is sent
        # or that the warning is no longer valid.

        response = messages.Header().decode(data)
        if response["split"] == messages.SPLIT:
            fragments = {}
            fragment = messages.Fragment.decode(response.payload)
            if fragment.is_compressed:
                raise NotImplementedError("Fragments are compressed")
            fragments[fragment["fragment_id"]] = fragment
            while len(fragments) < fragment["fragment_count"]:
                data = valve.source.BaseQuerier.get_response(self)
                fragment = messages.Fragment.decode(
                    messages.Header.decode(data).payload)
                fragments[fragment["fragment_id"]] = fragment
            return b"".join([frag[1].payload for frag in
                            sorted(fragments.items(), key=lambda f: f[0])])
        return response.payload

    def ping(self):
        """Ping the server, returning the round-trip latency in milliseconds

        The A2A_PING request is deprecated so this actually sends a A2S_INFO
        request and times that. The time difference between the two should
        be negligble.
        """

        time_sent = monotonic.monotonic()
        self.request(messages.InfoRequest())
        messages.InfoResponse.decode(self.get_response())
        time_received = monotonic.monotonic()
        return (time_received - time_sent) * 1000.0

    def info(self):
        """Retreive information about the server state

        This returns the response from the server which implements
        ``__getitem__`` for accessing response fields. For example:

        .. code:: python

            with ServerQuerier(...) as server:
                print(server.info()["server_name"])

        The following fields are available on the response:

        +--------------------+------------------------------------------------+
        | Field              | Description                                    |
        +====================+================================================+
        | response_type      | Always ``0x49``                                |
        +--------------------+------------------------------------------------+
        | server_name        | The name of the server                         |
        +--------------------+------------------------------------------------+
        | map                | The name of the map being ran by the server    |
        +--------------------+------------------------------------------------+
        | folder             | The *gamedir* if the modification being ran by |
        |                    | the server. E.g. ``tf``, ``cstrike``, ``csgo``.|
        +--------------------+------------------------------------------------+
        | game               | A string identifying the game being ran by the |
        |                    | server                                         |
        +--------------------+------------------------------------------------+
        | app_id             | The numeric application ID of the game ran by  |
        |                    | the server. Note that this is the app ID of the|
        |                    | client, not the server. For example, for Team  |
        |                    | Fortress 2 ``440`` is returned instead of      |
        |                    | ``232250`` which is the ID of the server       |
        |                    | software.                                      |
        +--------------------+------------------------------------------------+
        | player_count       | Number of players currently connected.         |
        |                    | See :meth:`.players` for caveats about the     |
        |                    | accuracy of this field.                        |
        +--------------------+------------------------------------------------+
        | max_players        | The number of player slots available. Note that|
        |                    | ``player_count`` may exceed this value under   |
        |                    | certain circumstances. See :meth:`.players`.   |
        +--------------------+------------------------------------------------+
        | bot_count          | The number of AI players present               |
        +--------------------+------------------------------------------------+
        | server_type        | A :class:`.util.ServerType` instance           |
        |                    | representing the type of server. E.g.          |
        |                    | Dedicated, non-dedicated or Source TV relay.   |
        +--------------------+------------------------------------------------+
        | platform           | A :class:`.util.Platform` instances            |
        |                    | represneting the platform the server is running|
        |                    | on. E.g. Windows, Linux or Mac OS X.           |
        +--------------------+------------------------------------------------+
        | password_protected | Whether or not a password is required to       |
        |                    | connect to the server.                         |
        +--------------------+------------------------------------------------+
        | vac_enabled        | Whether or not Valve anti-cheat (VAC) is       |
        |                    | enabled                                        |
        +--------------------+------------------------------------------------+
        | version            | The version string of the server software      |
        +--------------------+------------------------------------------------+

        Currently the *extra data field* (EDF) is not supported.
        """

        self.request(messages.InfoRequest())
        return messages.InfoResponse.decode(self.get_response())

    def players(self):
        """Retrive a list of all players connected to the server

        The following fields are available on the response:

        +--------------------+------------------------------------------------+
        | Field              | Description                                    |
        +====================+================================================+
        | response_type      | Always ``0x44``                                |
        +--------------------+------------------------------------------------+
        | player_count       | The number of players listed                   |
        +--------------------+------------------------------------------------+
        | players            | A list of player entries                       |
        +--------------------+------------------------------------------------+

        The ``players`` field is a list that contains ``player_count`` number
        of :class:`..messages.PlayerEntry` instances which have the same
        interface as the top-level response object that is returned.

        The following fields are available on each player entry:

        +--------------------+------------------------------------------------+
        | Field              | Description                                    |
        +====================+================================================+
        | name               | The name of the player                         |
        +--------------------+------------------------------------------------+
        | score              | Player's score at the time of the request.     |
        |                    | What this relates to is dependant on the       |
        |                    | gamemode of the server.                        |
        +--------------------+------------------------------------------------+
        | duration           | Number of seconds the player has been          |
        |                    | connected as a float                           |
        +--------------------+------------------------------------------------+

        .. note::
            Under certain circumstances, some servers may return a player
            list which contains empty ``name`` fields. This can lead to
            ``player_count`` being misleading.

            Filtering out players with empty names may yield a more
            accurate enumeration of players:

            .. code-block:: python

                with ServerQuerier(...) as query:
                    players = []
                    for player in query.players()["players"]:
                        if player["name"]:
                            players.append(player)
                    player_count = len(players)
        """

        # TF2 and L4D2's A2S_SERVERQUERY_GETCHALLENGE doesn't work so
        # just use A2S_PLAYER to get challenge number which should work
        # fine for all servers
        self.request(messages.PlayersRequest(challenge=-1))
        challenge = messages.GetChallengeResponse.decode(self.get_response())
        self.request(messages.PlayersRequest(challenge=challenge["challenge"]))
        return messages.PlayersResponse.decode(self.get_response())

    def rules(self):
        """Retreive the server's game mode configuration

        This method allows you capture a subset of a server's console
        variables (often referred to as 'cvars',) specifically those which
        have the ``FCVAR_NOTIFY`` flag set on them. These cvars are used to
        indicate game mode's configuration, such as the gravity setting for
        the map or whether friendly fire is enabled or not.

        The following fields are available on the response:

        +--------------------+------------------------------------------------+
        | Field              | Description                                    |
        +====================+================================================+
        | response_type      | Always ``0x56``                                |
        +--------------------+------------------------------------------------+
        | rule_count         | The number of rules                            |
        +--------------------+------------------------------------------------+
        | rules              | A dictionary mapping rule names to their       |
        |                    | corresponding string value                     |
        +--------------------+------------------------------------------------+
        """

        self.request(messages.RulesRequest(challenge=-1))
        challenge = messages.GetChallengeResponse.decode(self.get_response())
        self.request(messages.RulesRequest(challenge=challenge["challenge"]))
        return messages.RulesResponse.decode(self.get_response())
