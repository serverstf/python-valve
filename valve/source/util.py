# -*- coding: utf-8 -*-
# Copyright (C) 2014 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import sys


class Platform(object):
    """A Source server platform identifier

    This class provides utilities for representing Source server platforms
    as returned from a A2S_INFO request. Each platform is ultimately
    represented by one of the following integers:

    +-----+----------+
    | ID  | Platform |
    +=====+==========+
    | 108 | Linux    |
    +-----+----------+
    | 109 | Mac OS X |
    +-----+----------+
    | 111 | Mac OS X |
    +-----+----------+
    | 119 | Windows  |
    +----------------+
    """

    def __init__(self, value):
        """Initialise the platform identifier

        The given ``value`` will be mapped to a numeric identifier. If the
        value is already an integer it must then it must exist in the table
        above else ValueError is returned.

        If ``value`` is a one character long string then it's ordinal value
        as given by ``ord()`` is used. Alternately the string can be either
        of the following:
            * Linux
            * Mac OS X
            * Windows
        """
        if isinstance(value, basestring):
            if len(value) == 1:
                value = ord(value)
            else:
                value = {
                    "linux": 108,
                    "mac os x": 111,
                    "windows": 119,
                }.get(value.lower())
                if value is None:
                    raise ValueError("Couldn't convert string {!r} to valid "
                                     "platform identifier".format(value))
        if value not in {108, 109, 111, 119}:
            raise ValueError("Invalid platform identifier {!r}".format(value))
        self.value = value

    def __repr__(self):
        return "<{self.__class__.__name__} " \
               "{self.value} '{self}'>".format(self=self)

    def __unicode__(self):
        return {
            108: "Linux",
            109: "Mac OS X",
            111: "Mac OS X",
            119: "Windows",
        }[self.value]

    def __str__(self):
        return unicode(self).encode(sys.getdefaultencoding())

    def __int__(self):
        return self.value

    def __eq__(self, other):
        """Check for equality between two platforms

        If ``other`` is not a Platform instance then an attempt is made to
        convert it to one using same approach as __init__. This means platforms
        can be compared against integers and strings. For example:

        ```
        >>>Platform(108) == "linux"
        True
        >>>Platform(109) == 109
        True
        >>>Platform(119) == "w"
        True
        ```

        Despite the fact there are two numerical identifers for Mac (109 and
        111) comparing either of them together will yield ``True``.
        """
        if not isinstance(other, Platform):
            other = Platform(other)
        if self.value == 109 or self.value == 111:
            return other.value == 109 or other.value == 11
        else:
            return self.value == other.value

    @property
    def os_name(self):
        """Convenience mapping to names returned by ``os.name``"""
        return {
            108: "posix",
            109: "posix",
            111: "posix",
            119: "nt",
        }[self.value]


Platform.LINUX = Platform(108)
Platform.MAC_OS_X = Platform(111)
Platform.WINDOWS = Platform(119)
