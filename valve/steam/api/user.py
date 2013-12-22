# -*- coding: utf-8 -*-
# Copyright (C) 2013 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)


import datetime

from .exceptions import SteamAPIError
from .util import APIObjectsIterator
from ..id import SteamID, SteamIDError


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
        self.update()

    def __eq__(self, other):
        if isinstance(other, SteamID):
            return self.id == other
        if hasattr(other, "id"):
            return self.id == other.id
        else:
            return object.__eq__(self, other)

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
