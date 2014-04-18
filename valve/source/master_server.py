# -*- coding: utf-8 -*-
# Copyright (C) 2013-2014 Oliver Ainsworth


from . import MASTER_SERVER_ADDR
from . import messages
from .server import BaseServerQuerier


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
