# -*- coding: utf-8 -*-
# Copyright (C) 2013 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)


import datetime

from .items import Inventory
from .exceptions import SteamAPIError
from .util import APIObjectsIterator, resolve_appid, appid_to_sym
from ..id import SteamID, SteamIDError


class _Inventories(object):

    def __init__(self, api, user):
        self.api = api
        self.user = user
        self.cache = {}

    def __getitem__(self, inv):
        """Get an Inventory instance corresponding to the given app

        ``inv`` can either be a a numeric application ID, one of the
        application ID constants from ``valve.steam.api``, or one of
        the following symbolic names as a string:
            * dota-test
            * payday
            * tf2
            * dota
            * portal
            * csgo-beta
            * csgo
            * portal-2
        """
        inv = resolve_appid(inv)
        if inv not in self.cache:
            self.cache[inv] = Inventory(self.api, self.user, inv)
        return self.cache[inv]

    def __iter__(self):
        """Generator of all available invetories"""
        for appid in appid_to_sym.keys():
            yield self[appid]


class User(object):
    """Represents a Steam user

    The methods provided here relate to the ISteamUser interface of the
    Steam Web API.

    Note that instantiation of this class will result in a request to
    API being made.

    The following attributes are available:
        :id: The user's SteamID.
    """

    OFFLINE = 0
    ONLINE = 1
    BUSY = 2
    AWAY = 3
    SNOOZE = 4
    LOOKING_TO_TRADE = 5
    LOOKING_TO_PLAY = 6

    PRIVATE = 1
    FRIENDS_ONLY = 2
    FRIENDS_OF_FRIENDS = 3
    USERS = 4
    PUBLIC = 5

    def __init__(self, api, id):
        self._api = api
        self.id = id
        self._bans = {}
        self.inventories = _Inventories(self._api, self)
        self.update()

    def __eq__(self, other):
        if isinstance(other, SteamID):
            return self.id == other
        if hasattr(other, "id"):
            return self.id == other.id
        else:
            return object.__eq__(self, other)

    @property
    def is_community_banned(self):
        if not self._bans:
            self._update_bans()
        return self._bans["CommunityBanned"]

    @property
    def is_vac_banned(self):
        if not self._bans:
            self._update_bans()
        return self._bans["VACBanned"]

    @property
    def is_trade_banned(self):
        if not self._bans:
            self._update_bans()
        return self._bans["EconomyBan"] not in ["none", "probation"]

    @property
    def is_on_trade_probation(self):
        if not self._bans:
            self._update_bans()
        return self._bans["EconomyBan"] == "probation"

    def _update_bans(self):
        """Fetch the ban status for the user

        Response includes ``CommunityBanned``, ``DaysSinceLastBan``,
        ``EconomyBan`` ("none", "probation", don't know what the
        string is for banned,) ``NumberOfVACBans``,  ``VACBanned``.
        """
        response = self._api.request("GET",
                                     "ISteamUser/GetPlayerBans",
                                     1, {"steamids": self.id.as_64()})
        self._bans = response["players"][0]

    def update(self):
        response = self._api.request("GET",
                                     "ISteamUser/GetPlayerSummaries",
                                     2, {"steamids": self.id.as_64()})
        player = response["response"]["players"][0]
        self.comment_permissions = "commentpermission" in player
        self.visibility = player["communityvisibilitystate"]
        self.last_logoff = datetime.datetime.fromtimestamp(
            player["lastlogoff"])
        time_created = player.get("timecreated")
        if time_created is not None:
            self.created = datetime.datetime.fromtimestamp(time_created)
        else:
            self.created = None
        self.city = player.get("loccityid")
        self.country = player.get("loccountrycode")
        self.state = player.get("locstatecode")
        self.display_name = player["personaname"]
        self.real_name = player.get("realname")
        self.status = player["personastate"]
        self.state_flags = player.get("personastateflags")
        groupid = player.get("primaryclanid")  # TODO: abstract
        if groupid is None:
            self.primary_group = None
        else:
            self.primary_group = SteamID.from_community_url(
                SteamID.base_community_url + "gid/" + groupid)
        self.avatars = {
            "32x32": player["avatar"],
            "64x64": player["avatarmedium"],
            "184x184": player["avatarfull"],
        }
        self.url = player["profileurl"]
        self.game_id = player.get("gameid")
        self.game_name = player.get("gameextrainfo")
        address = player.get("gameserverip")
        if address is not None:
            host, port = address.split(":")
            port = int(port)
            self.game_server = (host, port)
        else:
            self.game_server = None
        if self._bans:
            self._update_bans()

    @property
    def is_ingame(self):
        if self.game_id is not None:
            return True
        else:
            return False

    def friends(self, relationship=None):
        params = {"steamid": self.id.as_64()}
        if relationship is not None:
            params["relationship"] = relationship
        response = self._api.request("GET",
                                     "ISteamUser/GetFriendList", 1, params)
        friends = []
        for friend in response["friendslist"]["friends"]:
            since = datetime.datetime.fromtimestamp(friend["friend_since"])
            relation = friend["relationship"]
            id = SteamID.from_community_url(
                SteamID.base_community_url + "id/" + friend["steamid"])
            friends.append([(self._api, id, self, since, relation), {}])
        return APIObjectsIterator(Friend, friends)

    def groups(self):
        """List of IDs for the groups the user is member to

        These are seemingly lacking in use beyond the sv_steamgroup
        convar for Source servers.
        """
        response = self._api.request("GET",
                                     "ISteamUser/GetUserGroupList",
                                     1, {"steamid": self.id.as_64()})
        if not response["response"]["success"]:
            raise SteamAPIError("Request was unsuccessful")
        return [int(group["gid"]) for group
                in response["response"]["groups"]]

class Friend(User):

    def __init__(self, api, id, friends_with, since, relationship):
        self.friends_with = friends_with
        self.friend_since = since
        self.relationship = relationship
        super(Friend, self).__init__(api, id)
