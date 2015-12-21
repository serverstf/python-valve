# -*- coding: utf-8 -*-
# Copyright (C) 2013-2015 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import socket
import select
import time

from . import messages


class NoResponseError(Exception):
    pass


class BaseServerQuerier(object):

    def __init__(self, address, timeout=5.0):
        self.host = address[0]
        self.port = address[1]
        self.timeout = timeout
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def request(self, request):
        self.socket.sendto(request.encode(), (self.host, self.port))

    def get_response(self):
        ready = select.select([self.socket], [], [], self.timeout)
        if not ready[0]:
            raise NoResponseError("Timed out waiting for response")
        try:
            data = ready[0][0].recv(1400)
        except socket.error as exc:
            raise NoResponseError(exc)
        return data


class ServerQuerier(BaseServerQuerier):
    """Implements the A2S Source server query protocol

    https://developer.valvesoftware.com/wiki/Server_queries
    """

    def request(self, request):
        header = messages.Header(split=messages.NO_SPLIT).encode()
        self.socket.sendto(header + request.encode(), (self.host, self.port))

    def get_response(self):

        data = BaseServerQuerier.get_response(self)

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
                data = BaseServerQuerier.get_response(self)
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

        t_send = time.time()
        self.request(messages.InfoRequest())
        messages.InfoResponse.decode(self.get_response())
        return (time.time() - t_send) * 1000.0

    def info(self):
        """Retreive information about the server state

        This returns the response from the server which implements
        ``__getitem__`` for accessing response fields. For example:

        .. code:: python

            server = ServerQuerier(...)
            print server.info()["server_name"]

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
        | player_count       | Number of players currently connected          |
        +--------------------+------------------------------------------------+
        | max_players        | The number of player slots available. Note that|
        |                    | ``player_count`` may exceed this value under   |
        |                    | certain circumstances.                         |
        +--------------------+------------------------------------------------+
        | bot_count          | The number of AI players present               |
        +--------------------+------------------------------------------------+
        | server_type        | A :class:`..util.ServerType` instance          |
        |                    | representing the type of server. E.g.          |
        |                    | Dedicated, non-dedicated or Source TV relay.   |
        +--------------------+------------------------------------------------+
        | platform           | A :class`..util.Platform` instances            |
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
