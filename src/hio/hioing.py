# -*- coding: utf-8 -*-
"""
hio.hioing module

Generic Constants and Classes
Exception Classes

"""
import sys
from collections import namedtuple

Versionage = namedtuple("Versionage", "major minor")

Version = Versionage(major=1, minor=0)  # KERI Protocol Version

SEPARATOR =  "\r\n\r\n"
SEPARATOR_BYTES = SEPARATOR.encode("utf-8")



class HioError(Exception):
    """
    Base Class for hio exceptions

    To use   raise HioError("Error: message")
    """


class ValidationError(HioError):
    """
    Validation related errors
    Usage:
        raise ValidationError("error message")
    """


class VersionError(ValidationError):
    """
    Bad or Unsupported Version

    Usage:
        raise VersionError("error message")
    """

class OglerError(HioError):
    """
    Error using or configuring Ogler

    Usage:
        raise OglerError("error message")
    """

class FilerError(HioError):
    """
    Error using or configuring Filer

    Usage:
        raise FilerError("error message")
    """


class Mixin():
    """
    Base class to enable consistent MRO for mixin multiple inheritance
    Allows each subclass to call
    super(MixinSubClass, self).__init__(*pa, **kwa)
    So the __init__ propagates to common top of Tree
    https://medium.com/geekculture/cooperative-multiple-inheritance-in-python-practice-60e3ac5f91cc
    """
    def __init__(self, *pa, **kwa):
        pass
