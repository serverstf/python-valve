# -*- coding: utf-8 -*-
# Copyright (C) 2013 Oliver Ainsworth

"""
    Implements a parser for the Valve Data Format (VDF,) or as often
    refered KeyValues.

    Currently only provides parsing functionality without the ability
    to serialise. API designed to mirror that of the built-in JSON
    module.

    https://developer.valvesoftware.com/wiki/KeyValues
"""

import string
import re

_KV_KEY = 0
_KV_BLOCK = 1
_KV_BLOCKEND = 2
_KV_PAIR = 3

ALWAYS = 0
UNQUOTED = 1
NEVER = 2


def coerce_type(token):
    """
        Attempts to convert a token to a native Python object by
        matching it against various regexes.

        Will silently fall back to string if no conversion can be made.

        Currently only capable of converting integers and floating point
        numbers.
    """

    regexes = [
        # regex, converter
        (r"^-?[0-9]+$", int),
        (r"^[-+]?[0-9]*\.?[0-9]+$", float),
        # TODO: ("rgb", pass),
        # TODO: ("hex triplet", pass),
        ]
    for regex, converter in regexes:
        print(regex, converter, token, re.match(regex, token, re.UNICODE))
        if re.match(regex, token, re.UNICODE):
            return converter(token)
    # Fallback to string
    return token


# Largely based on necavi's https://github.com/necavi/py-keyvalues
def loads(src, encoding=None, coerce_=UNQUOTED):
    """
        Loades a VDF string into a series of nested dictionaries.

            encoding -- The encoding of the given source string if not
                        Unicode. If this is not set and a bytestring is
                        given, ASCII will be the assumed encoding.

            corece_ -- can be set to determine whether an attempt should
                        be made to convert values to native Python type
                        equivalents.

                        If set to UNQUOTED (default,) only values that
                        are not enclosed in double quotes will be
                        converted.

                        If set to ALWAYS, will attempt to convert
                        regardless of whether the value is quoted or not.
                        not recommended.

                        If set to NEVER, no attempt will be made to
                        convert. Should produce most reliable behaviour.
    """

    if isinstance(src, str) and encoding is None:
        encoding = "ascii"
    if encoding is not None:
        src = src.decode(encoding)
    # else:
    #   assume unicode
    # pair type, pair key, pair value, coerce
    pairs = [[_KV_BLOCK, "", None, False]]
    # _KV_KEY -- all tokens begin as this
    # _KV_BLOCK -- is for when a _KV_KEY is followed by a {
    # _KV_PAIR -- is for when a _KV_KEY is followed by another token
    extended_alphanumeric = set(
        string.ascii_letters.decode("ascii") +
        unicode(string.digits) +
        u".-_")
    i = 0
    line = 1
    col = 0
    token = None
    try:
        while i < len(src):
            char = src[i]
            # Whitespace
            if char in {u" ", u"\t"}:
                pass
            # End-of-line
            elif char == u"\n":
                try:
                    if src[i+1] == u"\r":  # Will IndexError at EOF
                        i += 1
                        col += 1
                    line += 1
                    col = 0
                except IndexError:
                    pass
            # End-of-line
            elif char == u"\r":
                try:
                    if src[i+1] == u"\n":  # Will IndexError at EOF
                        i += 1
                        col += 1
                    line += 1
                    col = 0
                except IndexError:
                    pass
            # Double-quotes enclosed token
            elif char == u"\"":

                token = u""
                while True:
                    i += 1
                    col += 1
                    char = src[i]
                    # I don't agree with the assertion in py-keyvalues
                    # that \n or \r should also terminate a token if
                    # its quoted.
                    if char == u"\"":
                        break
                    elif char in {"\r", "\n"}:
                        raise SyntaxError("End-of-line quoted token")
                    elif char == u"\\":
                        i += 1
                        try:
                            escaped_char = src[i]
                        except IndexError:
                            raise SyntaxError("EOF in escaped character")
                        try:
                            char = {
                                u"n": u"\n",
                                u"r": u"\r",
                                u"t": u"\t",
                                u"\"": u"\"",
                                u"\\": u"\\",
                            }[escaped_char]
                        except KeyError:
                            raise SyntaxError("Invalid escape character")
                    token += char
                if pairs[-1][0] == _KV_KEY:
                    pairs[-1][0] = _KV_PAIR
                    pairs[-1][2] = token
                    pairs[-1][3] = coerce_ in [ALWAYS]
                else:
                    pairs.append([_KV_KEY, token, None, False])
            # Unquoted token
            elif char in extended_alphanumeric:
                token = u""
                while True:
                    token += char
                    i += 1
                    col += 1
                    char = src[i]
                    if char not in extended_alphanumeric:
                        # Assume end of token; in most cases this will
                        # white space or a new line

                        # If newline, rewind 1 char so it can be
                        # properly handled by the end-of-line processors
                        if char in {u"\n", u"\r"}:
                            i -= 1
                            col -= 1
                            char = src[i]
                        break
                if pairs[-1][0] == _KV_KEY:
                    pairs[-1][0] = _KV_PAIR
                    pairs[-1][2] = token
                    pairs[-1][3] = coerce_ in [ALWAYS, UNQUOTED]
                else:
                    pairs.append([_KV_KEY, token, None, False])
                # I don't know if there are any cases where an unquoted
                # key may be illegal, e.g. if it contains only digits.
                # I assume it is, but I won't handle it for now.
            # Block start
            elif char == u"{":
                if pairs[-1][0] != _KV_KEY:
                    raise SyntaxError("Block doesn't follow block name")
                pairs[-1][0] = _KV_BLOCK
            elif char == u"}":
                pairs.append([_KV_BLOCKEND, None, None, False])
            else:
                raise SyntaxError("Unexpected character")
            i += 1
            col += 1
    except SyntaxError as exc:
        raise ValueError("{} '{}'; line {} column {}".format(
            exc.message, src[i], line, col))
    dict_ = {}
    dict_stack = [dict_]
    CURRENT = -1
    PREVIOUS = -2
    for type, key, value, should_coerce in pairs[1:]:
        if type == _KV_BLOCK:
            dict_stack.append({})
            dict_stack[PREVIOUS][key] = dict_stack[CURRENT]
        elif type == _KV_BLOCKEND:
            dict_stack = dict_stack[:CURRENT]
        elif type == _KV_PAIR:
            dict_stack[CURRENT][key] = (coerce_type(value) if
                                        should_coerce else value)
        # else:
        #   should never occur, but would be caused by a token not being
        #   followed by a block or value
    return dict_


def load(fp, encoding=None, coerce_=UNQUOTED):
    """
        Same as loads but takes a file-like object as the source.
    """
    return loads(fp.read(), encoding, coerce_)


def dumps(obj, encoding=None, indent=u"    ", object_encoders={}):
    """
        Serialises a series of nested dictionaries to the VDF/KeyValues
        format and returns it as a string.

        If 'encoding' isn't specified a Unicode string will be returned,
        else an ecoded bytestring will be.

        'indent' is the string to be used to indent nested blocks. The
        string given should be Unicode and represent one level of
        indentation. Four spaces by default.

        'object_encoders' maps a series of types onto serialisers, which
        convert objects to their VDF equivalent. If no encoder is
        specified for a type it'll fall back to using __unicode__.
        Note that currently this likely causes None to be encoded
        incorrectly. Also, floats which include the exponent in their
        textual representaiton may also be 'wrong.'
    """

    object_codecs = {
        float: lambda v: unicode(repr(v / 1.0)),
    }
    object_codecs.update(object_encoders)
    # I don't know how TYPE_NONE (None) are meant to be encoded so we
    # just use unicode() until it's known.
    lines = []

    def recurse_obj(obj, indent_level=0):
        ind = indent * indent_level
        for key, value in obj.iteritems():
            if isinstance(value, dict):
                lines.append(u"{}\"{}\"".format(ind, key))
                lines.append(u"{}{{".format(ind))
                recurse_obj(value, indent_level + 1)
                lines.append(u"{}}}".format(ind))
            else:
                lines.append(u"{}\"{}\"{}\"{}\"".format(
                             ind,
                             key,
                             indent,
                             object_codecs.get(type(value), unicode)(value),
                             ))

    recurse_obj(obj)
    if encoding is not None:
        return u"\n".join(lines).encode(encoding)
    else:
        return u"\n".join(lines)


def dump(obj, fp, encoding, indent=u"    ", object_encoders={}):
    """
        Same as dumps but takes a file-like object 'fp' which will be
        written to.
    """

    return fp.write(dumps(obj, encoding, indent, object_encoders))
