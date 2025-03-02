# -*- encoding: utf-8 -*-
"""
hio.core.multidoing Module

Provides multiprocessing support



"""
import os
import time
import logging
import multiprocessing as mp

from collections import deque, namedtuple
from dataclasses import dataclass, astuple, asdict, field


from . import tyming
from .doing import Doist, Doer
from .. import hioing
from .. import help
from ..help import timing, helping
from ..help.helping import RawDom
from ..help import ogling

ogler = ogling.initOgler(prefix='hio_mp', name="Boss", level=logging.DEBUG)
logger = ogler.getLogger()

# BossDoer info to be injected in CrewDoer as BossDoer enter time
#    name (str | None): name of Boss for resource management
#    path (str | None): UXD cmd memo path used by crew to talk to their boss
Bossage = namedtuple("Bossage", "name path")

# BossDoer info to be injected into CrewDoer spinup containing both crew doist
# parms for Process target kwargs and and CrewDoer parms
#    name (str): child doist identifier for resources.
#    tyme (float): child doist start tyme
#    tock (float | None): child doist tock, tyme lag between runs
#    real (bool): child doist True means run in real time, tyme is real time
#    limit (float | None): child doist tyme limit. None means run forever
#    doers (list[Doers]): child doist List of Doers
#    temp (bool | None): True means use temporary file resources
#    boss (Bossage | None): BossDoer  info for CrewDoer. May be filled at enter time
#                       CrewDoer uses to contact BossDoer.
Loadage = namedtuple("Loadage", "name tyme tock real limit doers temp boss")


@dataclass
class CrewDom(RawDom):
    """Configuration dataclass of crew subprocess Doist parameters for crew doist
    and its CrewDoer to be injected by BossDoer.
    Use this when storing configuration in database or file. Use RawDom
    serialization hidden methods:

    Inherited Class Methods:
        _fromdict(cls, d: dict): return dataclass converted from dict d
        __iter__(self): asdict(self)
        _asdict(self): return self converted to dict
        _asjson(self): return self converted to json
        _ascbor(self): return self converted to cbor
        _asmgpk(self): return self converted to mgpk

    Attributes:
        name (str): child doist identifier for resources.
        tyme (float): child doist start tyme
        tock (float | None): child doist tock, tyme lag between runs
        real (bool): child doist True means run in real time, tyme is real time
        limit (float | None): child doist tyme limit. None means run forever
        doers (list[Doers]): child doist List of Doers
        temp (bool | None): True means use temporary file resources
        boss (Bossage | None): BossDoer  info for CrewDoer. May be filled at enter time
                                CrewDoer uses to contact BossDoer.
    """
    name: str ='child'  # unique identifier of child process and associated resources
    tyme: float = 0.0    # child doist start tyme
    tock: float | None = None  # child doist tyme lag between runs, None means ASAP
    real: bool = True  # child doist True means run in real time, tyme is real time
    limit: float | None = None  # child doist tyme limit. None mean run forever
    doers: list = field(default_factory=list)  # child doist list of doers
    temp: bool | None = False  # use temporary file resources if any
    boss: (Bossage | None) = Bossage(name=None, path=None)  # BossDoer info




class BossDoer(Doer):
    """BossDoer spawns multiple crew hand subprocesses and injects each with
    a Doist and Doers. The boss Doists runs the BossDoer in the parent process.
    Each crew hand Doist runs a CrewDoer that coordinates with the BossDoer.

    Analogy Boss runs a Crew of Hans. The parent process has a boss Doist which
    runs a BossDoer. Each crew hand is a child process with its own crew doist
    that runs its own CrewDoer

    See Doer for inherited attributes, properties, and methods.

    Inherited Attributes:
        done (bool): completion state:
                     True means completed fully. Otherwise incomplete.
                     Incompletion value may be None or False.
        opts (dict): schedulaer injects options from .opts into its .do generator
                     function as **opts parameter.


    Inherited Properties:
        tyme (float): is float relative cycle time of associated Tymist .tyme obtained
            via injected .tymth function wrapper closure.
        tymth (closure): function wrapper closure returned by Tymist.tymen()
                        method. When .tymth is called it returns associated
                        Tymist.tyme. Provides injected dependency on Tymist
                        tyme base.
        tock (float): desired time in seconds between runs or until next run,
                 non negative, zero means run asap


    Inherited Methods:
        __call__()  makes instance callable as generator function returning generator
        do() generator method that returns generator
        enter() is enter context action method
        recur() recur context action method or generator method
        clean() clean context action method
        exit() exit context method
        close() close context method
        abort() abort context method
        wind()  injects ._tymth dependency from associated Tymist to get its .tyme


    Attributes:
        name (str): unique identifier for this MultDoer boss
                    used to manage local resources

        loads (list[dict]): BossDoer info to be injected into CrewDoer spinup
                            containing both crew doist parmss for Process target
                            kwargs and and CrewDoer parms
                            (see Loadage._asdict() or CrewDom._asdict())
        ctx (mp.context.SpawnContext | None): context under which to spawn processes
        crew (dict): values are child Process instances keyed by name


    Properties:


    """

    def __init__(self, *, name='boss', loads=None, temp=False, **kwa):
        """Initialize instance.


        Inherited Parameters:
            tymth (closure): injected function wrapper closure returned by
                Tymist.tymen() instance. Calling tymth() returns associated
                Tymist.tyme.
            tock (float): seconds initial value of .tock
            opts (dict): injected options into its .do generator by scheduler

        Parameters:
            name (str): unique identifier for this BossDoer boss to be used
                        to manage local resources
            loads (list[dict]): parameters used to spinup crew hand subprocess
                                see fields of
            temp (bool): True means logger or other resources in spinup uses temp
                         False other wise

        """
        super(BossDoer, self).__init__(**kwa)
        self.name = name
        self.loads = loads if loads is not None else []
        self.temp = temp

        self.ctx = mp.get_context('spawn')
        self.crew = {}



    def enter(self, *, temp=None):
        """Do 'enter' context actions.
        Start processes with config from .tots
        Not a generator method.
        Set up resources. Comparable to context manager enter.

        Parameters:
            temp (bool | None): True means use temporary file resources if any.
                                None means ignore parameter value. Use self.temp.

        Inject temp or self.temp into file resources here if any

        Doist or DoDoer winds its doers on enter

        """
        logger.info("Boss Enter: name=%s size=%d, ppid=%d, pid=%d, module=%s, ogler=%s.",
            self.name, len(self.loads), os.getppid(), os.getpid(), __name__, ogler.name)
        self.count = 0
        for load in self.loads:
            hand = self.ctx.Process(name=load["name"],
                                     target=self.spinup,
                                     kwargs=load)
            self.crew[hand.name] = hand
            hand.start()


    def recur(self, tyme):
        """"""
        self.count += 1

        if not self.ctx.active_children():
            return True   # complete
        return False  # incomplete recur again


    def exit(self):
        """"""
        self.count += 1
        logger.info("Boss Exit: name=%s, ppid=%d, pid=%d, module=%s, ogler=%s.",
                self.name, os.getppid(), os.getpid(), __name__, ogler.name)


    def close(self):
        """"""
        self.count += 1


    def abort(self, ex):
        """"""
        self.count += 1


    @staticmethod
    def spinup(*, name='crew', tyme=0.0, tock=None, real=True, limit=None,
               doers=None, temp=None, boss=None):
        """Process target function to make and run doist after crew subprocess has
        been started.

        Parameters:
            name (str): unique crew hand name to be used to manage resources
            tyme (float): crew doist initial value of cycle time in seconds
            tock (float | None): crew doist tock time in seconds. None means run Asap
            real (bool): crew doist True means run in real time,
                        Otherwise run faster than real
            limit (float | None): crew doist seconds for max run time of doist.
                                  None means no limit.
            doers (iterable[Doer] | None): crew doist Doer class instances
                                   First entry must be CrewDoer
            temp (bool | None): True means use temp file resources by injection.
                                Otherwise ignore do not inject.
            boss (Bossage | None): boss info. May be filled at enter time
                                  CrewDoer uses to contact BossDoer.


        Doist must be built after process started so local tymth closure is created
        inside subprocess so that when doist winds the tyme for its doers
        the tymth closure is locally sourced.
        """
        # When run inside subprocess, spinup is at the outside scope for any
        # Doist and doers that reference ogler. This is a copy of the ogler in
        # the parer so can change ogler.level, ogler.temp and run ogler.reopen
        # to reopen log file or pass in temp to reopen
        ogler.level = logging.INFO
        ogler.reopen(name=name, temp=temp)
        logger = ogler.getLogger()

        logger.info("Crew Start: name=%s, ppid=%d, pid=%s, module=%s, ogler=%s.",
                        name, os.getppid(), os.getpid(), __name__, ogler.name)
        time.sleep(0.01)

        doist = Doist(name=name, tyme=tyme, tock=tock, real=real, limit=limit,
                      doers=doers, temp=temp)
        doist.do()

        logger.info("Crew End: name=%s, ppid=%d, pid=%s, module=%s, ogler=%s.",
                        name, os.getppid(), os.getpid(), __name__, ogler.name)


class CrewDoer(Doer):
    """CrewDoer runs interface between a given crew hand subprocess and its
    boss process. This must be first doer run by crew hand subprocess doist.

    Attributes:
        name (str): crew hand name for managing local resources to subprocess

    """

    def __init__(self, *, name='crew', **kwa):
        """
        Initialize instance.
        """
        super(CrewDoer, self).__init__(**kwa)
        self.name = name
        self.count = None


    def enter(self, *, temp=None):
        """Do 'enter' context actions. Override in subclass. Not a generator method.
        Set up resources. Comparable to context manager enter.


        Parameters:
            temp (bool | None): True means use temporary file resources if any
                                None means ignore parameter value. Use self.temp

        Inject temp or self.temp into file resources here if any

        Inject temp into file resources here if any

        Doist or DoDoer winds its doers on enter
        """
        self.count = 0
        #ogler.level = logging.INFO
        #ogler.reopen(name=self.name, temp=temp)
        logger = ogler.getLogger()
        logger.info("CrewDoer Enter: name=%s pid=%d, ogler=%s, count=%d.",
                    self.name, os.getpid(), ogler.name, self.count)


    def recur(self, tyme):
        """"""
        self.count += 1
        logger = ogler.getLogger()
        logger.info("CrewDoer Recur: name=%s, pid=%d, ogler=%s, count=%d.",
                    self.name, os.getpid(), ogler.name, self.count)
        if self.count > 3:
            return True  # complete
        return False  # incomplete

    def exit(self):
        """"""
        self.count += 1
        logger = ogler.getLogger()
        logger.info("CrewDoer Exit: name=%s pid=%d, ogler=%s, count=%d.",
                    self.name, os.getpid(), ogler.name, self.count)

    def close(self):
        """"""
        self.count += 1


    def abort(self, ex):
        """"""
        self.count += 1
