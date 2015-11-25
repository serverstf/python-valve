# -*- coding: utf-8 -*-
# Copyright (C) 2013-2014 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import six

from . import a2s
from . import messages
from . import util


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


class MasterServerQuerier(a2s.BaseServerQuerier):
    """Implements the Source master server query protocol

    https://developer.valvesoftware.com/wiki/Master_Server_Query_Protocol
    """

    def __init__(self, address=MASTER_SERVER_ADDR, timeout=10.0):
        super(MasterServerQuerier, self).__init__(address, timeout)

    def __iter__(self):
        """An unfitlered iterator of all Source servers

        This will issue a request for an unfiltered set of server addresses
        for each region. Addresses are received in batches but returning
        a completely unfiltered set will still take a long time and be
        prone to timeouts.

        .. note::
            If a request times out then the iterator will terminate early.
            Previous versions would propagate a :exc:`NoResponseError`.

        See :meth:`.find` for making filtered requests.
        """
        return self.find(region="all")

    def _query(self, region, filter_string):
        """Issue a request to the master server

        Returns a generator which yields ``(host, port)`` addresses as
        returned by the master server.

        Addresses are returned in batches therefore multiple requests may be
        dispatched. Because of this any of these requests may result in a
        :exc:`NotResponseError` raised. In such circumstances the iterator
        will exit early. Otherwise the iteration continues until the final
        address is reached which is indicated by the master server returning
        a 0.0.0.0:0 address.

        .. note::
            The terminating 0.0.0.0:0 is not yielded by the iterator.

        ``region`` should be a valid numeric region identifier and
        ``filter_string`` should be a formatted filter string as described
        on the Valve develper wiki:

        https://developer.valvesoftware.com/wiki/Master_Server_Query_Protocol#Filter
        """
        last_addr = "0.0.0.0:0"
        first_request = True
        while first_request or last_addr != "0.0.0.0:0":
            first_request = False
            self.request(messages.MasterServerRequest(region=region,
                                                      address=last_addr,
                                                      filter=filter_string))
            try:
                raw_response = self.get_response()
            except a2s.NoResponseError:
                return
            else:
                response = messages.MasterServerResponse.decode(raw_response)
                for address in response["addresses"]:
                    last_addr = "{}:{}".format(
                        address["host"], address["port"])
                    if not address.is_null:
                        yield address["host"], address["port"]

    def _map_region(self, region):
        """Convert string to numeric region identifier

        If given a non-string then a check is performed to ensure it is a
        valid region identifier. If it's not, ValueError is raised.

        Returns a list of numeric region identifiers.
        """
        if isinstance(region, six.text_type):
            try:
                regions = {
                    "na-east": [REGION_US_EAST_COAST],
                    "na-west": [REGION_US_WEST_COAST],
                    "na": [REGION_US_EAST_COAST, REGION_US_WEST_COAST],
                    "sa": [REGION_SOUTH_AMERICA],
                    "eu": [REGION_EUROPE],
                    "as": [REGION_ASIA, REGION_MIDDLE_EAST],
                    "oc": [REGION_AUSTRALIA],
                    "af": [REGION_AFRICA],
                    "rest": [REGION_REST],
                    "all": [REGION_US_EAST_COAST,
                            REGION_US_WEST_COAST,
                            REGION_SOUTH_AMERICA,
                            REGION_EUROPE,
                            REGION_ASIA,
                            REGION_AUSTRALIA,
                            REGION_MIDDLE_EAST,
                            REGION_AFRICA,
                            REGION_REST],
                }[region.lower()]
            except KeyError:
                raise ValueError(
                    "Invalid region identifer {!r}".format(region))
        else:
            # Just assume it's an integer identifier, we'll validate below
            regions = [region]
        for reg in regions:
            if reg not in {REGION_US_EAST_COAST,
                           REGION_US_WEST_COAST,
                           REGION_SOUTH_AMERICA,
                           REGION_EUROPE,
                           REGION_ASIA,
                           REGION_AUSTRALIA,
                           REGION_MIDDLE_EAST,
                           REGION_AFRICA,
                           REGION_REST}:
                raise ValueError("Invalid region identifier {!r}".format(reg))
        return regions

    def find(self, region="all", **filters):
        """Find servers for a particular region and set of filtering rules

        This returns an iterator which yields ``(host, port)`` server
        addresses from the master server.

        ``region`` spcifies what regions to restrict the search to. It can
        either be a ``REGION_`` constant or a string identifying the region.
        Alternately a list of the strings or ``REGION_`` constants can be
        used for specifying multiple regions.

        The following region identification strings are supported:

        +---------+-----------------------------------------+
        | String  | Region(s)                               |
        +=========+=========================================+
        | na-east | East North America                      |
        +---------+-----------------------------------------+
        | na-west | West North America                      |
        +---------+-----------------------------------------+
        | na      | East North American, West North America |
        +---------+-----------------------------------------+
        | sa      | South America                           |
        +---------+-----------------------------------------+
        | eu      | Europe                                  |
        +---------+-----------------------------------------+
        | as      | Asia, the Middle East                   |
        +---------+-----------------------------------------+
        | oc      | Oceania/Australia                       |
        +---------+-----------------------------------------+
        | af      | Africa                                  |
        +---------+-----------------------------------------+
        | rest    | Unclassified servers                    |
        +---------+-----------------------------------------+
        | all     | All of the above                        |
        +---------+-----------------------------------------+

        .. note::
            "``rest``" corresponds to all servers that don't fit with any
            other region. What causes a server to be placed in this region
            by the master server isn't entirely clear.

        The region strings are not case sensitive. Specifying an invalid
        region identifier will raise a ValueError.

        As well as region-based filtering, alternative filters are supported
        which are documented on the Valve developer wiki.

        https://developer.valvesoftware.com/wiki/Master_Server_Query_Protocol#Filter

        This method accepts keyword arguments which are used for building the
        filter string that is sent along with the request to the master server.
        Below is a list of all the valid keyword arguments:

        +------------+-------------------------------------------------------+
        | Filter     | Description                                           |
        +============+=======================================================+
        | type       | Server type, e.g. "dedicated". This can be a          |
        |            | ``ServerType`` instance or any value that can be      |
        |            | converted to a ``ServerType``.                        |
        +------------+-------------------------------------------------------+
        | secure     | Servers using Valve anti-cheat (VAC). This should be  |
        |            | a boolean.                                            |
        +------------+-------------------------------------------------------+
        | gamedir    | A string specifying the mod being ran by the server.  |
        |            | For example: ``tf``, ``cstrike``, ``csgo``, etc..     |
        +------------+-------------------------------------------------------+
        | map        | Which map the server is running.                      |
        +------------+-------------------------------------------------------+
        | linux      | Servers running on Linux. Boolean.                    |
        +------------+-------------------------------------------------------+
        | empty      | Servers which are not empty. Boolean.                 |
        +------------+-------------------------------------------------------+
        | full       | Servers which are full. Boolean.                      |
        +------------+-------------------------------------------------------+
        | proxy      | SourceTV relays only. Boolean.                        |
        +------------+-------------------------------------------------------+
        | napp       | Servers not running the game specified by the given   |
        |            | application ID. E.g. ``440`` would exclude all TF2    |
        |            | servers.                                              |
        +------------+-------------------------------------------------------+
        | noplayers  | Servers that are empty. Boolean                       |
        +------------+-------------------------------------------------------+
        | white      | Whitelisted servers only. Boolean.                    |
        +------------+-------------------------------------------------------+
        | gametype   | Server which match *all* the tags given. This should  |
        |            | be set to a list of strings.                          |
        +------------+-------------------------------------------------------+
        | gamedata   | Servers which match *all* the given hidden tags.      |
        |            | Only applicable for L4D2 servers.                     |
        +------------+-------------------------------------------------------+
        | gamedataor | Servers which match *any* of the given hidden tags.   |
        |            | Only applicable to L4D2 servers.                      |
        +------------+-------------------------------------------------------+

        .. note::
            Your mileage may vary with some of these filters. There's no
            real guarantee that the servers returned by the master server will
            actually satisfy the filter. Because of this it's advisable to
            explicitly check for compliance by querying each server
            individually. See :mod:`valve.source.a2s`.
        """
        if isinstance(region, (int, six.text_type)):
            regions = self._map_region(region)
        else:
            regions = []
            for reg in region:
                regions.extend(self._map_region(reg))
        filter_ = {}
        for key, value in six.iteritems(filters):
            if key in {"secure", "linux", "empty",
                       "full", "proxy", "noplayers", "white"}:
                value = int(bool(value))
            elif key in {"gametype", "gamedata", "gamedataor"}:
                value = [six.text_type(elt)
                         for elt in value if six.text_type(elt)]
                if not value:
                    continue
                value = ",".join(value)
            elif key == "napp":
                value = int(value)
            elif key == "type":
                if not isinstance(value, util.ServerType):
                    value = util.ServerType(value).char
                else:
                    value = value.char
            filter_[key] = six.text_type(value)
        # Order doesn't actually matter, but it makes testing easier
        filter_ = sorted(filter_.items(), key=lambda pair: pair[0])
        filter_string = "\\".join([part for pair in filter_ for part in pair])
        if filter_string:
            filter_string = "\\" + filter_string
        for region in regions:
            for address in self._query(region, filter_string):
                yield address
