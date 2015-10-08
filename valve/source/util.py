# -*- coding: utf-8 -*-
# Copyright (C) 2014-2015 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import sys

import six


class Platform(object):
    """A Source server platform identifier

    This class provides utilities for representing Source server platforms
    as returned from a A2S_INFO request. Each platform is ultimately
    represented by one of the following integers:

    +-----+----------+
    | ID  | Platform |
    +=====+==========+
    | 76  | Linux    |
    +-----+----------+
    | 108 | Linux    |
    +-----+----------+
    | 109 | Mac OS X |
    +-----+----------+
    | 111 | Mac OS X |
    +-----+----------+
    | 119 | Windows  |
    +-----+----------+

    .. note::
        Starbound uses 76 instead of 108 for Linux in the old GoldSource
        style.
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
        if isinstance(value, six.text_type):
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
        if value not in {76, 108, 109, 111, 119}:
            raise ValueError("Invalid platform identifier {!r}".format(value))
        self.value = value

    def __repr__(self):
        return "<{self.__class__.__name__} " \
               "{self.value} '{self}'>".format(self=self)

    def __unicode__(self):
        return {
            76: "Linux",
            108: "Linux",
            109: "Mac OS X",
            111: "Mac OS X",
            119: "Windows",
        }[self.value]

    if six.PY3:
        def __str__(self):
            return self.__unicode__()

        def __bytes__(self):
            return self.__unicode__().encode(sys.getdefaultencoding())
    else:
        def __str__(self):
            return self.__unicode__().encode(sys.getdefaultencoding())

    def __int__(self):
        return self.value

    def __eq__(self, other):
        """Check for equality between two platforms

        If ``other`` is not a Platform instance then an attempt is made to
        convert it to one using same approach as :meth:`__init__`. This means
        platforms can be compared against integers and strings. For example:

        .. code:: pycon

            >>>Platform(108) == "linux"
            True
            >>>Platform(109) == 109
            True
            >>>Platform(119) == "w"
            True

        Despite the fact there are two numerical identifers for Mac (109 and
        111) comparing either of them together will yield ``True``.

        .. code:: pycon

            >>>Platform(109) == Platform(111)
            True
        """
        if not isinstance(other, Platform):
            other = Platform(other)
        if self.value == 76 or self.value == 108:
            return other.value == 76 or other.value == 108
        elif self.value == 109 or self.value == 111:
            return other.value == 109 or other.value == 111
        else:
            return self.value == other.value

    @property
    def os_name(self):
        """Convenience mapping to names returned by ``os.name``"""
        return {
            76: "posix",
            108: "posix",
            109: "posix",
            111: "posix",
            119: "nt",
        }[self.value]


Platform.LINUX = Platform(108)
Platform.MAC_OS_X = Platform(111)
Platform.WINDOWS = Platform(119)


class ServerType(object):
    """A Source server platform identifier

    This class provides utilities for representing Source server types
    as returned from a A2S_INFO request. Each server type is ultimately
    represented by one of the following integers:

    +-----+---------------+
    | ID  | Server type   |
    +=====+===============+
    | 68  | Dedicated     |
    +-----+---------------+
    | 100 | Dedicated     |
    +-----+---------------+
    | 108 | Non-dedicated |
    +-----+---------------+
    | 112 | SourceTV      |
    +-----+---------------+

    .. note::
        Starbound uses 68 instead of 100 for a dedicated server in the old
        GoldSource style.
    """

    def __init__(self, value):
        """Initialise the server type identifier

        The given ``value`` will be mapped to a numeric identifier. If the
        value is already an integer it must then it must exist in the table
        above else ValueError is returned.

        If ``value`` is a one character long string then it's ordinal value
        as given by ``ord()`` is used. Alternately the string can be either
        of the following:

        * Dedicated
        * Non-Dedicated
        * SourceTV
        """
        if isinstance(value, six.text_type):
            if len(value) == 1:
                value = ord(value)
            else:
                value = {
                    "dedicated": 100,
                    "non-dedicated": 108,
                    "sourcetv": 112,
                }.get(value.lower())
                if value is None:
                    raise ValueError("Couldn't convert string {!r} to valid "
                                     "server type identifier".format(value))
        if value not in {68, 100, 108, 112}:
            raise ValueError(
                "Invalid server type identifier {!r}".format(value))
        self.value = value

    def __repr__(self):
        return "<{self.__class__.__name__} " \
               "{self.value} '{self}'>".format(self=self)

    def __unicode__(self):
        return {
            68: "Dedicated",
            100: "Dedicated",
            108: "Non-Dedicated",
            112: "SourceTV",
        }[self.value]

    if six.PY3:
        def __str__(self):
            return self.__unicode__()

        def __bytes__(self):
            return self.__unicode__().encode(sys.getdefaultencoding())
    else:
        def __str__(self):
            return self.__unicode__().encode(sys.getdefaultencoding())

    def __int__(self):
        return self.value

    def __eq__(self, other):
        """Check for equality between two server types

        If ``other`` is not a ServerType instance then an attempt is made to
        convert it to one using same approach as :meth:`.__init__`. This means
        server types can be compared against integers and strings. For example:

        .. code:: pycon

            >>>Server(100) == "dedicated"
            True
            >>>Platform(108) == 108
            True
            >>>Platform(112) == "p"
            True
        """
        if not isinstance(other, ServerType):
            other = ServerType(other)
        if self.value == 68 or self.value == 100:
            return other.value == 68 or other.value == 100
        else:
            return self.value == other.value

    @property
    def char(self):
        return chr(self.value)


ServerType.DEDICATED = ServerType(100)
ServerType.NON_DEDICATED = ServerType(108)
ServerType.SOURCETV = ServerType(112)
