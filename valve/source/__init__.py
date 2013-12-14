# -*- coding: utf-8 -*-
# Copyright (C) 2013 Oliver Ainsworth

"""
    Provides an interface for querying a Source server's state. Support
    for Goldsource currently not implmented.

    An interface for querying the 'Master Server' is also provided.
"""

import socket
import select
import time

from steam.servers import messages

NO_SPLIT = -1
SPLIT = -2

REGION_US_EAST_COAST = 0x00
REGION_US_WEST_COAST = 0x01
REGION_SOUTH_AMERICA = 0x02
REGION_EUROPE = 0x03
REGION_ASIA = 0x04
REGION_AUSTRALIA = 0x05
REGION_MIDDLE_EAST = 0x06
REGION_AFRICA = 0x07
REGION_REST = 0xFF

MASTER_SERVER_ADDR = ("hl2master.steampowered.com", 27011)


class BrokenMessageError(Exception):
    pass


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

    def request(self, request):
        self.socket.sendto(
            messages.Header(split=NO_SPLIT).encode() + request.encode(),
            (self.host, self.port)
        )

    def get_response(self):

        data = BaseServerQuerier.get_response(self)

        # According to https://developer.valvesoftware.com/wiki/Server_queries
        # "TF2 currently does not split replies, expect A2S_PLAYER and
        # A2S_RULES to be simply cut off after 1260 bytes."
        #
        # However whilst testing get_info() on a TF2 server, it did
        # set the split header to -2. So it is unclear whether the
        # warning means that only one fragment of the message is sent
        # or that the warning is no longer valid.

        response = messages.Header().decode(data)
        if response["split"] == SPLIT:
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
            return "".join([frag[1].payload for frag in
                            sorted(fragments.items(), key=lambda f: f[0])])
        return response.payload

    def ping(self):
        """
            Pings the server returning the latency in milliseconds. High
            probability that this straight up won't work as A2A_PING
            is seemingly deprecated. If it is indeed unavailable,
            NoResponseError will be raised.
        """

        t_send = time.time()
        self.request(messages.PingRequest())
        messages.PingResponse.decode(self.get_response())

        return (time.time() - t_send) / 1000.0

    def get_info(self):
        """
            Retrieves information about the server including,
            but not limited to: its name, the map currently being
            played, and the number of players.
        """

        self.request(messages.InfoRequest())
        return messages.InfoResponse.decode(self.get_response())

    def get_challenge(self):
        """
            Retrieves the 'challenge number' needed when making
            further A2S_PLAYER and A2S_RULES requests. However it is
            pretty much completely broken and is only provided for
            the sake of completeness.
        """

        self.request(messages.GetChallengeRequest())
        return messages.GetChallengeResponse.decode(self.get_response())

    def get_players(self):
        """
            Implements A2S_PLAYER. Retreives a list of current players
            on the server as well as their score and time-connected
            (in seconds).
        """

        # TF2 and L4D2's A2S_SERVERQUERY_GETCHALLENGE doesn't work so
        # just use A2S_PLAYER to get challenge number which should work
        # fine for all servers
        self.request(messages.PlayersRequest(challenge=-1))
        challenge = messages.GetChallengeResponse.decode(self.get_response())
        self.request(messages.PlayersRequest(challenge=challenge["challenge"]))
        return messages.PlayersResponse.decode(self.get_response())

    def get_rules(self):
        """
            Implementes A2S_RULES. Retrieves the current server
            configuration as expressed in terms of a series of
            name-value pairs.

            There's a fair chance a NotImplentedError exception will be
            raised as fragmented message handling is not implemented
            and A2S_RULES responses are generally quite long.
        """

        self.request(messages.RulesRequest(challenge=-1))
        challenge = messages.GetChallengeResponse.decode(self.get_response())
        self.request(messages.RulesRequest(challenge=challenge["challenge"]))
        return messages.RulesResponse.decode(self.get_response())


class MasterServerQuerier(BaseServerQuerier):

    def __init__(self, address=MASTER_SERVER_ADDR, timeout=10.0):
        BaseServerQuerier.__init__(self, address, timeout)

    def get_region(self, region_code, filter="", last_addr="0.0.0.0:0"):
        while True:
            self.request(messages.MasterServerRequest(region=region_code,
                                                      address=last_addr,
                                                      filter=filter))
            response = messages.MasterServerResponse.decode(
                self.get_response())
            for address in response["addresses"]:
                last_addr = "{}:{}".format(address["host"], address["port"])
                if address.is_null:
                    break
                yield address["host"], address["port"]
            if last_addr == "0.0.0.0:0":
                break
