# -*- encoding: utf-8 -*-
"""hio.core.hier.acting Module

Provides hierarchical action support

"""
from __future__ import annotations  # so type hints of classes get resolved later

from collections.abc import Callable
from collections import namedtuple

from ... import hioing
from ...hioing import Mixin, HierError
from ...help import Mine, Renam
from .hiering import Context, ActBase, register
from .needing import Need
from . import boxing




@register()
class Act(ActBase):
    """Act is generic subclass of ActBase meant for do verb acts.

    Inherited Class Attributes:
        Registry (dict): subclass registry whose items are (name, cls) where:
                name is unique name for subclass
                cls is reference to class object
        Names (dict): instance registry whose items are (name, instance) where:
                name is unique instance name and instance is instance reference

    Overridden Class Attributes
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.


    Inherited Properties:
        name (str): unique name string of instance
        iops (dict): input-output-parameters for .act
        context (str): action context for .act

    Hidden
        ._name (str|None): unique name of instance
        ._iopts (dict): input-output-paramters for .act
        ._context (str): action context for .act

    """
    Index = 0  # naming index for default names of this subclasses instances
    Aliases = ()  # aliases other names under which this subclass is registered

    @classmethod
    def _reregister(cls):
        """Reregisters cls after clear.
        Need to override in each subclass with super to reregister the class hierarchy
        """
        super(Act, cls)._reregister()
        Act.registerbyname()
        for name in Act.Aliases:
            Act.registerbyname(name)


    def __init__(self, stuff=None, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            context (str|None): action context for .act. Default is "enter"

        Parameters:
            stuff (None): TBD


        """
        super(Act, self).__init__(**kwa)
        self.stuff = stuff



    def act(self, **iops):
        """Act called by Actor. Should override in subclass."""

        return None  # conditional not met


@register()
class Tract(ActBase):
    """Tract (transit act) is subclass of ActBase whose .act evaluates conditional
    need expression to determine if a transition condition is satified for
    transition to its destination box.

    Inherited Class Attributes:
        Registry (dict): subclass registry whose items are (name, cls) where:
                name is unique name for subclass
                cls is reference to class object
        Names (dict): instance registry whose items are (name, instance) where:
                name is unique instance name and instance is instance reference

    Overridden Class Attributes
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.


    Inherited Properties:
        name (str): unique name string of instance
        iops (dict): input-output-parameters for .act
        context (str): action context for .act

    Attributes:
        dest (Box): destination Box for this transition.
        need (Need): transition condition to be evaluated

    Hidden
        ._name (str|None): unique name of instance
        ._iopts (dict): input-output-paramters for .act
        ._context (str): action context for .act

    """
    Index = 0  # naming index for default names of this subclasses instances
    Aliases = ()  # aliases other names under which this subclass is registered

    @classmethod
    def _reregister(cls):
        """Reregisters cls after clear.
        Need to override in each subclass with super to reregister the class hierarchy
        """
        super(Tract, cls)._reregister()
        Tract.registerbyname()
        for name in Tract.Aliases:
            Tract.registerbyname(name)


    def __init__(self, dest=None, need=None, context=Context.transit, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            context (str): action context for .act

        Parameters:
            dest (None|str|Box): destination Box for this transition.
                When None then resolve later to next box of current box
                When str is box name then resolve to box with that name
                When Box instance then use directly
            need (None|str|Need): transition condition to be evaluated
                When None then always evaluates to True
                When str = bool expression then create Need from expression
                When Need instance then use directly

        """
        super(Tract, self).__init__(context=context, **kwa)
        self.dest = dest  # fix this so default is next
        self.need = need if need is not None else Need()  # default need evals to True



    def act(self, **iops):
        """Act called by Actor. Should override in subclass."""
        if self.need():
            if not isinstance(self.dest, boxing.Box):
                raise HierError(f"Unresolved dest={self.dest}")
            return self.dest
        else:
            return None

