# -*- encoding: utf-8 -*-
"""
tests.help.test_helping module

"""
import pytest

import fractions
from dataclasses import dataclass, astuple, asdict, field
import json
import msgpack
import cbor2 as cbor

from hio.help import helping, Hict, Reat
from hio.help.helping import isign, sceil

def test_utilities():
    """
    Test utility functions
    """
    assert isign(1) == 1
    assert isign(-1) == -1
    assert isign(0) == 0
    assert isign(2) == 1
    assert isign(-1) == -1

    assert isign(1.0) == 1
    assert isign(-1.0) == -1
    assert isign(0.0) == 0

    assert isign(1.5) == 1
    assert isign(-1.5) == -1
    assert isign(0.5) == 1
    assert isign(-0.5) == -1


    assert sceil(0.5) == 1
    assert sceil(-0.5) == -1
    assert sceil(1) == 1
    assert sceil(-1) == -1
    assert sceil(0) == 0
    assert sceil(0.0) == 0

    assert sceil(1.1) == 2
    assert sceil(-1.1) == -2
    assert sceil(2.8) == 3
    assert sceil(-2.8) == -3

    assert sceil(fractions.Fraction(3, 2)) == 2
    assert sceil(fractions.Fraction(-3, 2)) == -2
    assert sceil(fractions.Fraction(0)) == 0



def test_copy_func():
    """
    Test the utility function for copying functions
    """
    def a(x=1):
        return x
    assert a() == 1
    assert a.__name__ == 'a'
    a.m = 2

    b = helping.copyfunc(a, name='b')
    assert b.__name__ == 'b'
    b.m = 4

    assert a.m != b.m
    assert a.__name__ == 'a'

    assert id(a) != id(b)

    """Done Test"""

def test_just():
    """
    Test just function
    """

    x = (1, 2, 3, 4)
    assert tuple(helping.just(3, x)) == (1, 2, 3)

    x = (1, 2, 3)
    assert tuple(helping.just(3, x)) == (1, 2, 3)

    x = (1, 2)
    assert tuple(helping.just(3, x)) == (1, 2, None)

    x = (1, )
    assert tuple(helping.just(3, x)) == (1, None, None)

    x = ()
    assert tuple(helping.just(3, x)) == (None, None, None)

def test_repack():
    """
    Test repack function
    """
    x = (1, 2, 3, 4)
    assert tuple(helping.repack(3, x)) == (1, 2, (3, 4))

    x = (1, 2, 3)
    assert tuple(helping.repack(3, x)) == (1, 2, (3,))

    x = (1, 2)
    assert tuple(helping.repack(3, x)) == (1, 2, ())

    x = (1, )
    assert tuple(helping.repack(3, x)) == (1, None, ())

    x = ()
    assert tuple(helping.repack(3, x)) == (None, None, ())



def test_non_string_iterable():
    """
    Test the metaclass NonStringIterable
    """
    a = bytearray(b'abc')
    w = dict(a=1, b=2, c=3)
    x = 'abc'
    y = b'abc'
    z = [1, 2, 3]

    assert isinstance(a, helping.NonStringIterable)
    assert isinstance(w, helping.NonStringIterable)
    assert not isinstance(x, helping.NonStringIterable)
    assert not isinstance(y, helping.NonStringIterable)
    assert isinstance(z, helping.NonStringIterable)


def test_non_string_sequence():
    """
    Test the metaclass NonStringSequence
    """
    a = bytearray(b'abc')
    w = dict(a=1, b=2, c=3)
    x = 'abc'
    y = b'abc'
    z = [1, 2, 3]

    assert isinstance(a, helping.NonStringSequence)
    assert not isinstance(w, helping.NonStringSequence)
    assert not isinstance(x, helping.NonStringSequence)
    assert not isinstance(y, helping.NonStringSequence)
    assert isinstance(z, helping.NonStringSequence)


def test_is_iterator():
    """
    Test the utility function isIterator
    """
    o = [1, 2, 3]
    assert not helping.isIterator(o)
    i = iter(o)
    assert helping.isIterator(i)

    def genf():
        yield ""
        yield ""

    assert not helping.isIterator(genf)
    gen = genf()
    assert helping.isIterator(gen)


def test_attributize():
    """
    Test the utility decorator attributize generator
    """
    #  use as function wrapper not decorator
    def gf(me, x):  # convention injected reference to attributed wrapper is 'me'
        me.x = 5
        me.y = 'a'
        cnt = 0
        while cnt < x:
            yield cnt
            cnt += 1

    agf = helping.attributize(gf)
    ag = agf(3)
    # body of gf is not run until first next call so attributes not set up yet
    assert helping.isIterator(ag)
    assert not hasattr(ag, 'x')
    assert not hasattr(ag, 'y')
    n = next(ag)  # attributes now set up
    assert n == 0
    assert hasattr(ag, 'x')
    assert hasattr(ag, 'y')
    assert ag.x == 5
    assert ag.y == 'a'
    n = next(ag)
    assert n == 1

    #  use as decorator
    # Set up like WSGI for generator function
    @helping.attributize
    def bar(me, req=None, rep=None):
        """
        Generator function with "skin" parameter for skin wrapper to
        attach attributes
        """
        me._status = 400
        me._headers = Hict(example="Hi")
        yield b""
        yield b""
        yield b"Hello There"
        return b"Goodbye"

    # now use it like WSGI server does
    global  headed  # gen is nonlocal not global nonlocals may be read but not assigned
    headed = False
    msgs = []
    gen = bar()
    assert helping.isIterator(gen)
    assert not hasattr(gen, '_status')
    assert not hasattr(gen, '_headers')

    def write(msg):
        """
        Simulate WSGI write
        """
        global headed  # because assinged

        if not headed:  # add headers
            if hasattr(gen, "_status"):  # nonlocal gen
                if gen._status is not None:
                    msgs.append(str(gen._status))
            if hasattr(gen, "_headers"):  # nonlocal gen
                for key, val in gen._headers.items():
                    msgs.append("{}={}".format(key, val))

            headed = True

        msgs.append(msg)

    assert headed == False
    igen = iter(gen)
    assert igen is gen  # already iterator to iter() call does nothing
    done = False
    while not done:
        try:
            msg = next(igen)  # assigns (creates) attributes with defaults
        except StopIteration as ex:
            if hasattr(ex, "value") and ex.value:
                write(ex.value)
            write(b'')  # in case chunked send empty chunk to terminate
            done = True
        else:
            if msg:  # only write if not empty allows async processing
                write(msg)

    assert headed == True
    assert msgs == ['400', 'example=Hi', b'Hello There', b'Goodbye', b'']


    # Set up like WSGI for generator method
    # use as decorator
    class R:
        @helping.attributize
        def bar(self, me, req=None, rep=None):
            """
            Generator function with "skin" parameter for skin wrapper to
            attach attributes
            """
            self.name = "Peter"
            me._status = 400
            me._headers = Hict(example="Hi")
            yield b""
            yield b""
            yield b"Hello There " + self.name.encode()
            return b"Goodbye"

    # now use it like WSGI server does
    headed = False
    r = R()
    msgs = []
    gen = r.bar()
    assert helping.isIterator(gen)
    # attributes not created yet
    assert not hasattr(gen, '_status')
    assert not hasattr(gen, '_headers')


    def write(msg):
        """
        Simulate WSGI write
        """
        global headed  # because assigned

        if not headed:  # add headers
            if hasattr(gen, "_status"):
                if gen._status is not None:  # nonlocal gen
                    msgs.append(str(gen._status))
            if hasattr(gen, "_headers"):  # nonlocal gen
                for key, val in gen._headers.items():
                    msgs.append("{}={}".format(key, val))

            headed = True

        msgs.append(msg)

    assert headed == False
    igen = iter(gen)
    assert igen is gen  # iter() call is innocuous
    done = False
    while not done:
        try:
            msg = next(igen)
        except StopIteration as ex:
            if hasattr(ex, "value") and ex.value:
                write(ex.value)
            write(b'')  # in case chunked send empty chunk to terminate
            done = True
        else:
            if msg:  # only write if not empty allows async processing
                write(msg)

    assert headed == True
    assert msgs == ['400', 'example=Hi', b'Hello There Peter', b'Goodbye', b'']


def test_ocfn_load_dump():
    """
    Test ocfn
    """
    #create temp file
    # helping.ocfn(path)

    """Done Test"""



def test_b64_helpers():
    """
    Test Base64 conversion utility routines
    """

    cs = helping.intToB64(0)
    assert cs == "A"
    i = helping.b64ToInt(cs)
    assert i == 0

    cs = helping.intToB64(0, l=0)
    assert cs == ""
    with pytest.raises(ValueError):
        i = helping.b64ToInt(cs)

    cs = helping.intToB64(None, l=0)
    assert cs == ""
    with pytest.raises(ValueError):
        i = helping.b64ToInt(cs)

    cs = helping.intToB64b(0)
    assert cs == b"A"
    i = helping.b64ToInt(cs)
    assert i == 0

    cs = helping.intToB64(27)
    assert cs == "b"
    i = helping.b64ToInt(cs)
    assert i == 27

    cs = helping.intToB64b(27)
    assert cs == b"b"
    i = helping.b64ToInt(cs)
    assert i == 27

    cs = helping.intToB64(27, l=2)
    assert cs == "Ab"
    i = helping.b64ToInt(cs)
    assert i == 27

    cs = helping.intToB64b(27, l=2)
    assert cs == b"Ab"
    i = helping.b64ToInt(cs)
    assert i == 27

    cs = helping.intToB64(80)
    assert cs == "BQ"
    i = helping.b64ToInt(cs)
    assert i == 80

    cs = helping.intToB64b(80)
    assert cs == b"BQ"
    i = helping.b64ToInt(cs)
    assert i == 80

    cs = helping.intToB64(4095)
    assert cs == '__'
    i = helping.b64ToInt(cs)
    assert i == 4095

    cs = helping.intToB64b(4095)
    assert cs == b'__'
    i = helping.b64ToInt(cs)
    assert i == 4095

    cs = helping.intToB64(4096)
    assert cs == 'BAA'
    i = helping.b64ToInt(cs)
    assert i == 4096

    cs = helping.intToB64b(4096)
    assert cs == b'BAA'
    i = helping.b64ToInt(cs)
    assert i == 4096

    cs = helping.intToB64(6011)
    assert cs == "Bd7"
    i = helping.b64ToInt(cs)
    assert i == 6011

    cs = helping.intToB64b(6011)
    assert cs == b"Bd7"
    i = helping.b64ToInt(cs)
    assert i == 6011

    s = "-BAC"
    b = helping.codeB64ToB2(s[:])
    assert len(b) == 3
    assert b == b'\xf8\x10\x02'
    t = helping.codeB2ToB64(b, 4)
    assert t == s[:]
    i = int.from_bytes(b, 'big')
    assert i == 0o76010002
    i >>= 2 * (len(s) % 4)
    assert i == 0o76010002
    p = helping.nabSextets(b, 4)
    assert p == b'\xf8\x10\x02'

    b = helping.codeB64ToB2(s[:3])
    assert len(b) == 3
    assert b == b'\xf8\x10\x00'
    t = helping.codeB2ToB64(b, 3)
    assert t == s[:3]
    i = int.from_bytes(b, 'big')
    assert i == 0o76010000
    i >>= 2 * (len(s[:3]) % 4)
    assert i == 0o760100
    p = helping.nabSextets(b, 3)
    assert p == b'\xf8\x10\x00'

    b = helping.codeB64ToB2(s[:2])
    assert len(b) == 2
    assert b == b'\xf8\x10'
    t = helping.codeB2ToB64(b, 2)
    assert t == s[:2]
    i = int.from_bytes(b, 'big')
    assert i == 0o174020
    i >>= 2 * (len(s[:2]) % 4)
    assert i == 0o7601
    p = helping.nabSextets(b, 2)
    assert p == b'\xf8\x10'

    b = helping.codeB64ToB2(s[:1])
    assert len(b) == 1
    assert b == b'\xf8'
    t = helping.codeB2ToB64(b, 1)
    assert t == s[:1]
    i = int.from_bytes(b, 'big')
    assert i == 0o370
    i >>= 2 * (len(s[:1]) % 4)
    assert i == 0o76
    p = helping.nabSextets(b, 1)
    assert p == b'\xf8'



    text = b"-A-Bg-1-3-cd"
    match = helping.Reb64.match(text)
    assert match
    assert match is not None

    text = b''
    match = helping.Reb64.match(text)
    assert match
    assert match is not None

    text = b'123#$'
    match = helping.Reb64.match(text)
    assert not match
    assert match is None

    """End Test"""




def test_reat():
    """Test regular expression Reat for attribute name """
    name = "hello"
    assert Reat.match(name)

    name = "_hello"
    assert Reat.match(name)

    name = "hell1"
    assert Reat.match(name)

    name = "1hello"
    assert not Reat.match(name)

    name = "hello.hello"
    assert not Reat.match(name)
    """Done Test"""



if __name__ == "__main__":
    test_utilities()
    test_attributize()
    test_b64_helpers()
    test_reat()
