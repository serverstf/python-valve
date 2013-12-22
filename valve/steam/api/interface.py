# -*- coding: utf-8 -*-
# Copyright (C) 2013 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import logging

import requests

log = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s",
                            level=logging.DEBUG)

    from . import SteamAPI
    from ..id import SteamID

    key = "5493480160076D1E988C8C20A50085AA"
    my_id =  SteamID.from_text("STEAM_0:0:44647673")
    api = SteamAPI(key)
    user = api.user(my_id)

