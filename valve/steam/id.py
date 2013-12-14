# -*- coding: utf-8 -*-
# Copyright (C) 2013 Oliver Ainsworth

"""
    Provides the ability to process and represent SteamIDs in multiple formats.
"""

import re
import urlparse
import warnings

# https://developer.valvesoftware.com/wiki/SteamID

UNIVERSE_INDIVIDUAL = 0
UNIVERSE_PUBLIC = 1
UNIVERSE_BETA = 2
UNIVERSE_INTERNAL = 3
UNIVERSE_DEV = 4
UNIVERSE_RC = 5

_universes = [
    UNIVERSE_INDIVIDUAL,
    UNIVERSE_PUBLIC,
    UNIVERSE_BETA,
    UNIVERSE_INTERNAL,
    UNIVERSE_DEV,
    UNIVERSE_RC,
    ]

TYPE_INVALID = 0
TYPE_INDIVIDUAL = 1
TYPE_MULTISEAT = 2
TYPE_GAME_SERVER = 3
TYPE_ANON_GAME_SERVER = 4
TYPE_PENDING = 5
TYPE_CONTENT_SERVER = 6
TYPE_CLAN = 7
TYPE_CHAT = 8
TYPE_P2P_SUPER_SEEDER = 9
TYPE_ANON_USER = 10

_types = [
    TYPE_INVALID,
    TYPE_INDIVIDUAL,
    TYPE_MULTISEAT,
    TYPE_GAME_SERVER,
    TYPE_ANON_GAME_SERVER,
    TYPE_PENDING,
    TYPE_CONTENT_SERVER,
    TYPE_CLAN,
    TYPE_CHAT,
    TYPE_P2P_SUPER_SEEDER,
    TYPE_ANON_USER,
    ]

type_letter_map = {
    TYPE_INDIVIDUAL: "U",
    TYPE_CLAN: "g",
    TYPE_CHAT: "T",
    }
letter_type_map = {v: k for k, v in type_letter_map.items()}

type_url_path_map = {
    TYPE_INDIVIDUAL: ["profiles", "id"],
    TYPE_CLAN: ["groups", "gid"],
    }

textual_id_regex = re.compile(r"^STEAM_(?P<X>\d+):(?P<Y>\d+):(?P<Z>\d+)$")
community32_regex = re.compile(r".*/(?P<path>{paths})/\[(?P<type>[{type_chars}]):1:(?P<W>\d+)\]$".format(paths="|".join("|".join(paths) for paths in type_url_path_map.values()), type_chars="".join(c for c in type_letter_map.values())))
community64_regex = re.compile(r".*/(?P<path>{paths})/(?P<W>\d+)$".format(paths="|".join("|".join(paths) for paths in type_url_path_map.values())))

class SteamIDError(Exception): pass
class SteamID(object):

    base_community_url = "http://steamcommunity.com/"

    @classmethod
    def from_community_url(cls, id, universe=UNIVERSE_INDIVIDUAL):
        """
            Takes a Steam community ID for a profile or group and converts
            it to a SteamID. The type of the ID is infered from the
            type character in 32-bit community urls ([U:1:1] for example)
            or from the URL path (/profile or /groups) for 64-bit URLs.

            As there is no way to determine the universe directly from
            URL it must be expliticly set, defaulting to UNIVERSE_INDIVIDUAL.

            Raises SteamIDError if the URL cannot be parsed.
        """

        url = urlparse.urlparse(id)

        match = community32_regex.match(url.path)
        if match:
            if match.group("path") not in type_url_path_map[letter_type_map[match.group("type")]]:
                warnings.warn("Community URL ({}) path doesn't match type character".format(url.path))

            w = int(match.group("W"))
            y = w & 1
            z = (w - y) / 2

            return cls(z, y, letter_type_map[match.group("type")], universe)

        match = community64_regex.match(url.path)
        if match:

            w = int(match.group("W"))
            y = w & 1

            if match.group("path") in type_url_path_map[TYPE_INDIVIDUAL]:
                z = (w - y - 0x0110000100000000) / 2
                type = TYPE_INDIVIDUAL
            elif match.group("path") in type_url_path_map[TYPE_CLAN]:
                z = (w - y - 0x0170000000000000) / 2
                type = TYPE_CLAN

            return cls(z, y, type, universe)

        raise SteamIDError("Invalid Steam community URL ({})".format(url))

    @classmethod
    def from_text(cls, id, type=TYPE_INDIVIDUAL):
        """
            Takes a teaxtual SteamID in the form STEAM_X:Y:Z and returns
            a SteamID instance. The X represents the account's 'universe,'
            Z is the account number and Y is either 1 or 0.

            As the account type cannot be directly infered from the
            SteamID it must be explicitly specified, defaulting to
            TYPE_INDIVIDUAL.

            The two special IDs STEAM_ID_PENDING and UNKNOWN are also
            handled returning SteamID instances with the appropriate
            types set (TYPE_PENDING and TYPE_INVALID respectively) and
            with all else set to 0.
        """

        if id == "STEAM_ID_PENDING":
            return cls(0, 0, TYPE_PENDING, 0)

        if id == "UNKNOWN":
            return cls(0, 0, TYPE_INVALID, 0)

        match = textual_id_regex.match(id)
        if not match:
            raise SteamIDError("ID '{}' doesn't match format {}".format(id, textual_id_regex.pattern))

        return cls(
            int(match.group("Z")),
            int(match.group("Y")),
            type,
            int(match.group("X"))
            )

    def __init__(self, account_number, instance, type, universe):

        if universe not in _universes:
            raise SteamIDError("Invalid universe {}".format(universe))

        if type not in _types:
            raise SteamIDError("Invalid type {}".format(type))

        if 0 < account_number > (2**32) - 1:
            raise SteamIDError("Account number ({}) out of range".format(account_number))

        if instance not in [1, 0]:
            raise SteamIDError("Expected instance to be 1 or 0, got {}".format(instance))

        self.account_number = account_number # Z
        self.instance = instance # Y
        self.type = type
        self.universe = universe # X

    @property
    def type_name(self):
        """
            Convenience method which maps the account type to a more
            meaningful name.
        """
        return {v: k for k, v in globals().iteritems() if k.startswith("TYPE_")}.get(self.type, self.type)

    def __str__(self):
        """
            Returns the textual representation of the SteamID in the form
            STEAM_X:Y:Z such that it can be parsed by SteamID.from_text
            and return an equivalent SteamID instance.

            STEAM_ID_PENDING and UNKNOWN returned as appropriate.
        """

        if self.type == TYPE_PENDING:
            return "STEAM_ID_PENDING"
        elif self.type == TYPE_INVALID:
            return "UNKNOWN"

        return "STEAM_{}:{}:{}".format(self.universe, self.instance, self.account_number)

    def __unicode__(self):
        return unicode(str(self))

    def __int__(self):
        """
            Returns the '64-bit representation' of the SteamID as given
            by account_number * 2 + instance + V, where V is dependant on
            the account type.

            Only valid for SteamIDs with type TYPE_INDIVIDUAL and
            TYPE_CLAN.
        """

        if self.type == TYPE_INDIVIDUAL:
            return (self.account_number * 2) + 0x0110000100000000 + self.instance
        elif self.type == TYPE_CLAN:
            return (self.account_number * 2) + 0x0170000000000000 + self.instance

        raise SteamIDError("Cannot create 64-bit identifier for SteamID with type {}".format(self.type_name))

    def __eq__(self, other):
        try:
            return (self.account_number == other.account_number and
                    self.instance == other.instance and
                    self.type == other.type and
                    self.universe == other.universe)
        except AttributeError:
            return False

    def __ne__(self, other):
        return not self == other

    def as_32(self):
        """
            Returns the 32-bit community ID for the SteamID. Only
            avilable for individual, clan/group and chat types.
        """

        try:
            return "[{}:1:{}]".format(
                                    type_letter_map[self.type],
                                    (self.account_number * 2) + self.instance
                                    )
        except KeyError:
            raise SteamIDError("Cannot create 32-bit indentifier for SteamID with type {}".format(self.type_name))

    def as_64(self):
        """
            Returns the 64-bit community ID of the SteamID. Same as
            __int__ but returns a string instead. Because of this it
            only available for TYPE_INDIVIDUAL and TYPE_CLAN.
        """
        return str(int(self))

    def community_url(self, id64=True):
        """
            Returns a fully qualified URL to the Steam community page
            relating to the SteamID. Can return either 64 (default) or
            32 bit community IDs.

            Only available for TYPE_INDIVIDUAL and TYPE_CLAN.
        """

        path_func = self.as_64 if id64 else self.as_32
        try:
            return urlparse.urljoin(
                        self.__class__.base_community_url,
                        "/".join((type_url_path_map[self.type][0], path_func()))
                        )
        except KeyError:
            raise SteamIDError("Cannot generate community URL for type {}".format(self.type_name))
