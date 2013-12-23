# -*- coding: utf-8 -*-
# Copyright (C) 2013 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)


class SchemaItem(object):

    def __init__(self, schema, item):
        self.schema = schema
        self.index = item["defindex"]
        self.name = item["item_name"]
        self.display_name = item["name"]

    def __repr__(self):
        return "<{} '{}' for '{}'>".format(
            self.__class__.__name__, self.name, self.schema.appid)


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
        return "<{} for '{}' with items>".format(self.__class__.__name__,
                                                 self.appid,
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
        for item_def in response["items"]:
            self.items.append(Item(item_def, self.schema))
