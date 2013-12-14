# -*- coding: utf-8 -*-
# Copyright (C) 2013 Oliver Ainsworth

"""
    Provides an interface for querying a Source server's state. Support
    for Goldsource currently not implmented.

    An interface for querying the 'Master Server' is also provided.
"""

NO_SPLIT = -1
SPLIT = -2

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
