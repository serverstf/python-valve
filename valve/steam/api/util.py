# -*- coding: utf-8 -*-
# Copyright (C) 2013 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)


DOTA2_TEST = 205790
PAYDAY2 = 218620
# Unknown 221540
# Unknown 238460
# Unknown 247040
# Unknown 247200
# Unknown 260
TF2 = 440
DOTA2 = 570
PORTAL2 = 620
CSGO_BETA = 710
CSGO = 730
# Unknown 816
PORTAL2_BETA = 841

appid_to_sym = {
    DOTA2_TEST: "dota-test",
    PAYDAY2: "payday",
    TF2: "tf2",
    DOTA2: "dota",
    PORTAL2: "portal",
    CSGO_BETA: "csgo-beta",
    CSGO: "csgo",
    PORTAL2_BETA: "portal-2",
}
sym_to_appid = {v: k for k, v in appid_to_sym.items()}

appid_to_name = {
    DOTA2_TEST: "Dota 2 Test",
    PAYDAY2: "Payday 2",
    TF2: "Team Fortress 2",
    DOTA2: "Dota 2",
    PORTAL2: "Portal 2",
    CSGO_BETA: "Counter-strike: Global Offensive beta",
    CSGO: "Counter-strike: Global Offensive",
    PORTAL2_BETA: "Portal 2 beta",
}
name_to_appid = {v: k for k, v in appid_to_name.items()}


def resolve_appid(appid):
    """Resolve an application ID to a numeric value

    If a string is given as ``appid``, then the corresponding app ID
    will be looked up in ``sym_to_appid`` and returned. If the app ID
    cannot be found KeyError is raised.
    """
    if isinstance(appid, int):
        return appid
    if appid.lower() in sym_to_appid:
        return sym_to_appid[appid.lower()]
    raise KeyError("Cannot resolve appid '{}'".format(appid))


class APIObjectsIterator(object):

    def __init__(self, cls, arguments=[]):
        self.cls = cls
        self.arguments = arguments

    def __iter__(self):

        def generator():
            for args, kwargs in self.arguments:
                yield self.cls(*args, **kwargs)

        return generator()

    def __repr__(self):
        return "<iterator of {} '{}.{}' objects>".format(
            len(self.arguments), self.cls.__module__, self.cls.__name__)
