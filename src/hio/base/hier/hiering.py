# -*- encoding: utf-8 -*-
"""
hio.core.hier.hiering Module

Provides hierarchical action support

"""
from __future__ import annotations  # so type hints of classes get resolved later

import os
import sys
import time
import logging
import json
import signal
import re
import multiprocessing as mp
import functools

from collections import deque, namedtuple
from collections.abc import Iterable, Mapping, Callable
from typing import Any, Type
from dataclasses import dataclass, astuple, asdict, field


from ..tyming import Tymee
from ... import hioing
from ...hioing import Mixin, HierError
from ...help import isNonStringIterable, MapDom, modify


# Regular expression to detect valid attribute names for Boxes
ATREX = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
# Usage: if Reat.match(name): or if not Reat.match(name):
Reat = re.compile(ATREX)  # compile is faster





# ToDo  any callable usually function that is not already a subclass of Actor.
# can be converted so a subclass of Actor and then registered in the Registry.
# normally if defining a class then inhereit from Actor. But if simply a function
# then decorate with actify so that a a new subclass is created and registered

def actify(name, *, base=None, attrs=None):
    """Parametrized decorator that converts the decorated function func into
    .act method of new subclass of class base with .__name__ name. If not
    provided then uses Act as base. When provided base must be subclass of Act.
    Registers new subclass in Act.Registry. Then instantiates cls and returns
    instance.

    Returns:
        instance (cls): instance of new subclass

    Updates the class attributes of new subclass with attrs if any.

    Usage:


    Assigning a function to a class the value of an attribute automatically
    makes that attribute a bound method with injected self as first argument.

    class A():
        def a(self):
           print(self)

    a = A()
    a.a()
    <__main__.A object at 0x1059ffc50>

    def b(self):
        print(self)

    A.b = b
    a.b()
    <__main__.A object at 0x1059ffc50>


    """
    base = base if base is not None else ActBase
    if not issubclass(base, ActBase):
        raise hioing.HierError(f"Expected Act subclass got {base=}.")

    attrs = attrs if attrs is not None else {}
    # assign Act attrs
    attrs.update(dict(Registry=base.Registry, Names=base.Names, Index=0))
    cls = type(name, (base, ), attrs)  # create new subclass of base of Act.
    register(cls)  # register subclass in cls.Registry

    def decorator(func):
        if not isinstance(func, Callable):
            raise hioing.HierError(f"Expected Callable got {func=}.")
        cls.act = func  # assign as bound method .act with injected self.

        @functools.wraps(func)
        def inner(*pa, **kwa):
            return cls(*pa, **kwa)  # instantiate and return instance
        return inner
    return decorator


def register(cls):
    """Class Decorator to add cls as cls.Registry entry for itself keyed by its
    own .__name__. Need class decorator so that class object is already created
    by registration time when decorator is applied
    """
    name = cls.__name__
    if name in cls.Registry:
        raise hioing.HierError(f"Act by {name=} already registered.")
    cls.Registry[name] = cls
    return cls


@register
class ActBase(Mixin):
    """Act Base Class. Callable with Registry of itself and its subclasses.

    Class Attributes:
        Registry (dict): subclass registry whose items are (name, cls) where:
                name is unique name for subclass
                cls is reference to class object
        Names (dict): instance registry whose items are (name, instance) where:
                name is unique instance name and instance is instance reference
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.



    Properties:
        name (str): unique name string of instance
        iops (dict): input-output-parameters for .act

    Hidden
        ._name (str|None): unique name of instance
        ._iopts (dict): input-output-paramters for .act

    """
    Registry = {}  # subclass registry
    Names = {}  # instance name registry
    Index = 0  # naming index for default names of this subclasses instances


    def __init__(self, *, name=None, iops=None, **kwa):
        """
        Initialization method for instance.

        Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.

        """
        super(ActBase, self).__init__(**kwa) # in case of MRO
        self.name = name  # set name property
        self._iops = iops if iops is not None else {}  #


    def __call__(self):
        """Make Actor instance a callable object. run its .act method"""
        return self.act(**self.iops)


    def act(self, **iops):
        """Act called by Actor. Should override in subclass."""
        return iops  # for debugging



    @property
    def name(self):
        """Property getter for ._name

        Returns:
            name (str): unique identifier of instance
        """
        return self._name


    @name.setter
    def name(self, name=None):
        """Property setter for ._name

        Paramaters:
            name (str|None): unique identifier of instance. When None generate
                unique name using .Index
        """
        while name is None or name in self.Names:
                name = self.__class__.__name__ + str(self.Index)
                self.__class__.Index += 1   # do not shadow class attribute

        if not Reat.match(name):
            raise HierError(f"Invalid {name=}.")

        self.Names[name] = self
        self._name = name


    @property
    def iops(self):
        """Property getter for ._iopts. Makes ._iopts read only

        Returns:
            iops (dict): input-output-parameters for .act
        """
        return self._iops




@dataclass
class WorkDom(MapDom):
    """WorkDom provides state for building boxwork by a boxer to be injected
    make methods of Boxer by workify wrapper.


    Attributes:
        box (Box | None): current box in box work. None if not yet a box
        over (Box | None): current over Box in box work. None if top level
        bxpre (str):  default box name prefix used to generate unique box name
                    relative to boxer.boxes
        bxidx (int): default box name index used to generate unique box name
                    relative to boxer.boxes
    """
    box: None | Box = None  # current box in boxwork. None if not yet any box
    over: None | Box = None  # current over box in boxwork. None if not yet any over
    bxpre: str = 'box'  # default box name prefix when name not provided
    bxidx: int = 0  # default box name index when name not provided





class Haul(dict):
    """Haul subclass of dict with custom methods dunder methods and get that
    will only allow actual keys as str. Iterables passed in as key are converted
    to a "_' joined str. Uses "_" so can use dict constuctor if need be with str
    path. Assumes items in Iterable do not contain '_'.

    Special staticmethods:
        tokeys(k) returns split of k at separator '_' as tuple.

    """
    def __init__(self, *pa, **kwa):
        """Convert keys that are tuples when positional argument is Iterable or
        Mapping to '.' joined strings

        dict __init__ signature options are:
            dict(**kwa)
            dict(mapping, **kwa)
            dict(iterable, **kwa)
        dict.update has same call signature
            d.update({"a": 5, "b": 2,}, c=3 , d=4)

        """
        self.update(*pa, **kwa)


    def __setitem__(self, k, v):
        return super(Haul, self).__setitem__(self.tokey(k), v)


    def __getitem__(self, k):
        return super(Haul, self).__getitem__(self.tokey(k))


    def __delitem__(self, k):
        return super(Haul, self).__delitem__(self.tokey(k))


    def __contains__(self, k):
        return super(Haul, self).__contains__(self.tokey(k))


    def get(self, k, default=None):
        if not self.__contains__(k):
            return default
        else:
            return self.__getitem__(k)



    def update(self, *pa, **kwa):
        """Convert keys that are tuples when positional argument is Iterable or
        Mapping to '.' joined strings

        dict __init__ signature options are:
            dict(**kwa)
            dict(mapping, **kwa)
            dict(iterable, **kwa)
        dict.update has same call signature
            d.update({"a": 5, "b": 2,}, c=3 , d=4)

        """
        if len(pa) > 1:
            raise TypeError(f"Expected 1 positional argument got {len(pa)}.")

        if pa:
            di = pa[0]
            if isinstance(di, Mapping):
                rd = {}
                for k, v in di.items():
                    rd[self.tokey(k)] = v
                super(Haul, self).update(rd, **kwa)

            elif isinstance(di, Iterable):
                ri = []
                for k, v in di:
                    ri.append((self.tokey(k), v))
                super(Haul, self).update(ri, **kwa)

            else:
                raise TypeError(f"Expected Mapping or Iterable got {type(di)}.")

        else:
            super(Haul, self).update(**kwa)


    @staticmethod
    def tokey(keys):
        """Joins tuple of strings keys to '.' joined string key. If already
        str then returns unchanged.

        Parameters:
            keys (Iterable[str] | str ): non-string Iteralble of path key
                    components to be '.' joined into key.
                    If keys is already str then returns unchanged

        Returns:
            key (str): '.' joined string
        """
        if isNonStringIterable(keys):
            try:
                key = '.'.join(keys)
            except Exception as ex:
                raise KeyError(ex.args) from ex
        else:
            key = keys
        if not isinstance(key, str):
            raise KeyError(f"Expected str got {key}.")
        return key


    @staticmethod
    def tokeys(key):
        """Converts '.' joined string key to tuple of keys by splitting on '.'

        Parameters:
            key (str): '.' joined string to be split
        Returns:
            keys (tuple[str]): split of key on '.' into path key components
        """
        return tuple(key.split("."))



