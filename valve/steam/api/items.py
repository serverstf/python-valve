# -*- coding: utf-8 -*-
# Copyright (C) 2013 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

from . import util
from . import exceptions


class SchemaItem(object):

    def __init__(self, schema, item):
        self.schema = schema
        self.index = item["defindex"]
        self.name = item["item_name"]
        self.display_name = item["name"]

    def __repr__(self):
        return "<{} '{}' for '{}'>".format(
            self.__class__.__name__, self.name,
            util.appid_to_name.get(self.schema.appid, self.schema.appid))


class Schema(object):

    def __init__(self, api, appid, language=None):
        self._api = api
        self.appid = appid
        params = {"language": language} if language is not None else {}
        response = self._api.request(
            "GET",
            "IEconItems_{}/GetSchema".format(appid), 1, params)["result"]
        self.qualities = {}
        for name, quality in response["qualities"].iteritems():
            self.qualities[quality] = name
        self.items = {}
        for item_def in response["items"]:
            item = SchemaItem(self, item_def)
            self.items[item.index] = item

    def __repr__(self):
        return "<{} for '{}' with {} items>".format(
            self.__class__.__name__,
            util.appid_to_name.get(self.appid, self.appid),
            len(self))

    def __iter__(self):
        return self.items.itervalues()

    def __len__(self):
        return len(self.items)


class Item(object):

    def __init__(self, item, schema):
        self._schema_item = schema.items[item["defindex"]]
        self.id = item["id"]
        self.original_id = item["original_id"]
        self.quality = item["quality"]

    def __repr__(self):
        return "<{} {} of {}>".format(self.__class__.__name__,
                                      self.id,
                                      self._schema_item)

    def __getattr__(self, attr):
        return getattr(self._schema_item, attr)

    @property
    def quality_name(self):
        return self._schema_item.schema.qualities[self.quality]


class Inventory(object):

    def __init__(self, api, user, appid):
        self._api = api
        self.appid = appid
        self.schema = Schema(api, appid)
        self.user = user
        self.items = []
        self.update()

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    @property
    def utilisation(self):
        return len(self) / self.capacity

    def update(self):
        response = self._api.request(
            "GET", "IEconItems_{}/GetPlayerItems".format(self.appid),
            1, {"steamid": self.user.id.as_64()})["result"]
        self.capacity = response["num_backpack_slots"]
        items = []
        for item_def in response["items"]:
            items.append(Item(item_def, self.schema))
        self.items = items


class TradingCard(object):

    _icon_root = "http://cdn.steamcommunity.com/economy/image/"

    def __init__(self, card, schema):
        self.id = int(card["id"])
        self.class_id = int(card["classid"])
        self.instance_id = int(card["instanceid"])
        self.quantity = int(card["amount"])
        schema_entry = schema["{}_{}".format(self.class_id,
                                             self.instance_id)]
        self.appid = int(schema_entry["market_fee_app"])
        self.name = schema_entry["market_hash_name"]
        self.display_name = schema_entry["market_name"]
        self.tradeable = bool(schema_entry["marketable"])
        self.icons = {
            "small": self._icon_root + schema_entry["icon_url"],
            "large": self._icon_root + schema_entry["icon_url_large"],
        }
        self.foil = False
        for tag in schema_entry["tags"]:
            # Should probably check that internal_name == item_class_2
            # To make sure it's actually a trading card
            if (tag["category"] == "cardborder"
                    and tag["internal_name"] == "cardborder_1"):
                self.foil = True

    def __repr__(self):
        return "<{} '{}'>".format(self.__class__.__name__, self.name,)


class TradingCards(object):

    def __init__(self, api, user):
        self._api = api
        self.appid = util.TRADING_CARDS
        self.user = user
        self.items = []
        self.update()

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)

    @property
    def utilisation(self):
        return 1.0

    def update(self):
        url = ("http://steamcommunity.com/profiles/"
               "{}/inventory/json/753/6".format(self.user.id.as_64()))
        response = self._api.session.request("GET", url).json()
        if not response["success"]:
            raise exceptions.SteamAPIError("Request was unsuccessful")
        items = []
        for card in response["rgInventory"].itervalues():
            items.append(TradingCard(card, response["rgDescriptions"]))
        self.items = items
