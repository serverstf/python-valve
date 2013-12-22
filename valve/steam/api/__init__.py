# -*- coding: utf-8 -*-
# Copyright (C) 2013 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import requests

from . import user
from .exceptions import SteamAPIError
from ..id import SteamID, SteamIDError


class SteamAPI(object):

    api_root = "http://api.steampowered.com"

    def __init__(self, key=None):
        self.key = key
        self.session = requests.Session()

    def request(self, method, path, version, params):
        params["key"] = self.key
        if not path.startswith("/"):
            path = "/" + path
        path += "/v{:04d}".format(version)
        response = self.session.request(method,
                                        self.api_root + path,
                                        params=params)
        if response.status_code != 200:
            raise SteamAPIError(
                "Request returned status {}".format(response.status_code))
        try:
            return response.json()
        except ValueError as exc:
            raise SteamAPIError(exc)

    def user(self, id):
        """Creates a User instance for the user referenced by ``id``

        ``id`` can either be a SteamID instance, a Steam community
        URL for a user or the vanity URL for a user. Note that the vanity
        URL should only be the tail component (the bit you can actually
        change as a user.)
        """
        if isinstance(id, SteamID):
            steamid = id
        else:
            try:
                steamid = SteamID.from_community_url(id)
            except SteamIDError:
                response = self.request("GET",
                                        "ISteamUSer/ResolveVanityURL",
                                        1, {"vanityurl": id})
                if response["response"]["success"] == 42:
                    raise SteamAPIError(
                        "Couldn't resolve vanity URL '{}'".format(id))
                steamid = SteamID.from_community_url(
                    SteamID.base_community_url +
                    "id/" + response["response"]["steamid"])
        return user.User(self, steamid)
