# -*- encoding: utf-8 -*-
"""
tests.core.test_memoing module

"""
from base64 import urlsafe_b64encode as encodeB64
from base64 import urlsafe_b64decode as decodeB64

import pytest

from hio.help import helping
from hio.base import doing, tyming
from hio.core.memo import memoing
from hio.core.memo import Versionage, Sizage, GramDex, SGDex, Memoer

def test_memoer_class():
    """Test class attributes of Memoer class"""

    assert Memoer.Version == Versionage(major=0, minor=0)
    assert Memoer.Codex == memoing.GramDex

    assert Memoer.Codes == {'Basic': '__', 'Signed': '_-'}
    assert Memoer.Names == {'__': 'Basic', '_-': 'Signed'}


    # Codes table with sizes of code (hard) and full primitive material
    assert Memoer.Sizes == {'__': Sizage(cs=2, ms=22, vs=0, ss=0, ns=4, hs=28),
                            '_-': Sizage(cs=2, ms=22, vs=44, ss=88, ns=4, hs=160)}


    #  verify all Codes
    for code, val in Memoer.Sizes.items():
        cs = val.cs
        ms = val.ms
        vs = val.vs
        ss = val.ss
        ns = val.ns
        hs = val.hs

        assert len(code) == cs == 2
        assert code[0] == '_'
        code[1] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz01234567890-_'
        assert hs > 0
        assert hs == cs + ms + vs + ss + ns
        assert ms  # ms must not be empty
        ps = (3 - ((ms) % 3)) % 3  # net pad size for mid
        assert ps == (cs % 4)  #  combined code + mid size must lie on 24 bit boundary
        assert not vs % 4   # vid size must be on 24 bit boundary
        assert not ss % 4   # sig size must be on 24 bit boundary
        assert ns and not ns % 4   # neck (num or cnt) size must be on 24 bit boundary
        assert hs and not hs % 4   # head size must be on 24 bit boundary
        if vs:
            assert ss  # ss must not be empty if vs not empty

    assert Memoer.Sodex == SGDex
    #assert Memoer.Bodes == {b'\xff\xf0': '__', b'\xff\xe0': '_-'}

    assert Memoer.MaxMemoSize == (2**32-1)  # absolute max memo payload size
    assert Memoer.MaxGramSize == (2**16-1)  # absolute max gram size
    assert Memoer.MaxGramCount == (2**24-1)  # absolute max gram count

    """Done Test"""


def test_memoer_basic():
    """Test Memoer class basic
    """
    peer = memoing.Memoer()
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc == 4
    assert peer.code == memoing.GramDex.Basic == '__'
    assert not peer.curt
    # (code, mid, vid, sig, neck, head) part sizes
    assert peer.Sizes[peer.code] == (2, 22, 0, 0, 4, 28)  # cs ms vs ss ns hs
    assert peer.size == peer.MaxGramSize
    assert not peer.verific

    peer.reopen()
    assert peer.opened == True

    assert not peer.txms
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    peer.service()
    assert peer.txbs == (b'', None)

    memo = "Hello There"
    dst = "beta"
    peer.memoit(memo, dst)
    assert peer.txms[0] == ('Hello There', 'beta', None)
    peer.serviceTxMemos()
    assert not peer.txms
    m, d = peer.txgs[0]
    assert not peer.wiff(m)  # base64
    assert m.endswith(memo.encode())
    assert d == dst == 'beta'
    peer.serviceTxGrams()
    assert not peer.txgs
    assert peer.txbs == (b'', None)

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms
    mid = '__ALBI68S1ZIxqwFOSWFF1L2'
    gram = (mid + 'AAAA' + 'AAAB' + "Hello There").encode()
    echo = (gram, "beta")
    peer.echos.append(echo)
    peer.serviceReceives(echoic=True)
    assert peer.rxgs[mid][0] == bytearray(b'Hello There')
    assert peer.counts[mid] == 1
    assert peer.sources[mid] == 'beta'
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert peer.rxms[0] == ('Hello There', 'beta', None)
    peer.serviceRxMemos()
    assert not peer.rxms

    # send and receive via echo
    memo = "See ya later!"
    dst = "beta"
    peer.memoit(memo, dst)
    assert peer.txms[0] == ('See ya later!', 'beta', None)
    peer.serviceTxMemos()
    assert not peer.txms
    m, d = peer.txgs[0]
    assert not peer.wiff(m)  # base64
    assert m.endswith(memo.encode())
    assert d == dst == 'beta'
    peer.serviceTxGrams(echoic=True)
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    assert peer.echos

    assert not peer.rxgs
    assert not peer.rxms
    assert not peer.counts
    assert not peer.sources
    peer.serviceReceives(echoic=True)
    mid = list(peer.rxgs.keys())[0]
    assert peer.rxgs[mid][0] == b'See ya later!'
    assert peer.counts[mid] == 1
    assert peer.sources[mid] == 'beta'
    assert not peer.echos
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    peer.rxms[0]
    assert peer.rxms[0] == ('See ya later!', 'beta', None)
    peer.serviceRxMemos()
    assert not peer.rxms

    # test binary q2 encoding of transmission gram header
    peer.curt = True  # set to binary base2
    assert peer.curt
    memo = "Hello There"
    dst = "beta"
    peer.memoit(memo, dst)
    assert peer.txms[0] == ('Hello There', 'beta', None)
    peer.serviceTxMemos()
    assert not peer.txms
    m, d = peer.txgs[0]
    assert peer.wiff(m)  # base2
    assert m.endswith(memo.encode())
    assert d == dst == 'beta'
    peer.serviceTxGrams()
    assert not peer.txgs
    assert peer.txbs == (b'', None)

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms
    mid = '__ALBI68S1ZIxqwFOSWFF1L2'
    headneck = decodeB64((mid + 'AAAA' + 'AAAB').encode())
    gram = headneck + b"Hello There"
    assert peer.wiff(gram)  # base2
    echo = (gram, "beta")
    peer.echos.append(echo)
    peer.serviceReceives(echoic=True)
    assert peer.rxgs[mid][0] == bytearray(b'Hello There')
    assert peer.counts[mid] == 1
    assert peer.sources[mid] == 'beta'
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert peer.rxms[0] == ('Hello There', 'beta', None)
    peer.serviceRxMemos()
    assert not peer.rxms

    peer.close()
    assert peer.opened == False
    """ End Test """


def test_memoer_small_gram_size():
    """Test Memoer class with small gram size
    """
    peer = memoing.Memoer(size=6)
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc == 4
    assert peer.code == memoing.GramDex.Basic == '__'
    assert not peer.curt
    # (code, mid, vid, sig, neck, head) part sizes
    assert peer.Sizes[peer.code] == (2, 22, 0, 0, 4, 28)  # cs ms vs ss ns hs
    assert peer.size == 33  # can't be smaller than head + neck + 1
    assert not peer.verific

    peer = memoing.Memoer(size=38)
    assert peer.size == 38
    peer.reopen()
    assert peer.opened == True

    assert not peer.txms
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    peer.service()
    assert peer.txbs == (b'', None)

    memo = "Hello There"
    dst = "beta"
    peer.memoit(memo, dst)
    assert peer.txms[0] == ('Hello There', 'beta', None)
    peer.serviceTxMemos()
    assert not peer.txms
    assert len(peer.txgs) == 2
    for m, d in peer.txgs:
        assert not peer.wiff(m)  # base64
        assert d == dst == 'beta'
    peer.serviceTxGrams()
    assert not peer.txgs
    assert peer.txbs == (b'', None)

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms
    b'__DFymLrtlZG6bp0HhlUsR6uAAAAAAACHello '
    b'__DFymLrtlZG6bp0HhlUsR6uAAABThere'
    mid = '__DFymLrtlZG6bp0HhlUsR6u'
    gram = (mid + 'AAAA' + 'AAAC' + "Hello ").encode()
    echo = (gram, "beta")
    peer.echos.append(echo)
    gram = (mid + 'AAAB' + "There").encode()
    echo = (gram, "beta")
    peer.echos.append(echo)
    peer.serviceReceives(echoic=True)
    assert len(peer.rxgs[mid]) == 2
    assert peer.counts[mid] == 2
    assert peer.sources[mid] == 'beta'
    assert peer.rxgs[mid][0] == bytearray(b'Hello ')
    assert peer.rxgs[mid][1] == bytearray(b'There')
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert peer.rxms[0] == ('Hello There', 'beta', None)
    peer.serviceRxMemos()
    assert not peer.rxms
    assert not peer.echos

    # send and receive via echo
    memo = "See ya later!"
    dst = "beta"
    peer.memoit(memo, dst)
    assert peer.txms[0] == ('See ya later!', 'beta', None)
    peer.serviceTxMemos()
    assert not peer.txms
    assert len(peer.txgs) == 2
    for m, d in peer.txgs:
        assert not peer.wiff(m)  # base64
        assert d == dst == 'beta'
    peer.serviceTxGrams(echoic=True)
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    assert peer.echos

    assert not peer.rxgs
    assert not peer.rxms
    assert not peer.counts
    assert not peer.sources
    peer.serviceReceives(echoic=True)
    assert not peer.echos
    mid = list(peer.rxgs.keys())[0]
    assert len(peer.rxgs[mid]) == 2
    assert peer.counts[mid] == 2
    assert peer.sources[mid] == 'beta'
    assert peer.rxgs[mid][0] == bytearray(b'See ya')
    assert peer.rxgs[mid][1] == bytearray(b' later!')
    assert not peer.echos
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    peer.rxms[0]
    assert peer.rxms[0] == ('See ya later!', 'beta', None)
    peer.serviceRxMemos()
    assert not peer.rxms

    # test binary q2 encoding of transmission gram header
    peer.curt =  True  # set to binary base2
    assert peer.curt
    assert peer.size == 38
    memo = 'See ya later alligator!'
    dst = "beta"
    peer.memoit(memo, dst)
    assert peer.txms[0] == ('See ya later alligator!', 'beta', None)
    peer.serviceTxMemos()
    assert not peer.txms
    assert len(peer.txgs) == 2
    for m, d in peer.txgs:
        assert peer.wiff(m)   # base2
        assert d == dst == 'beta'
    peer.serviceTxGrams()
    assert not peer.txgs
    assert peer.txbs == (b'', None)

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms
    assert not peer.echos

    b'__DFymLrtlZG6bp0HhlUsR6uAAAAAAACHello '
    b'__DFymLrtlZG6bp0HhlUsR6uAAABThere'
    mid = '__DFymLrtlZG6bp0HhlUsR6u'
    headneck = decodeB64((mid + 'AAAA' + 'AAAC').encode())
    gram = headneck + b"See ya later a"
    assert peer.wiff(gram)   # base2
    echo = (gram, "beta")
    peer.echos.append(echo)
    head = decodeB64((mid + 'AAAB').encode())
    gram = head + b"lligator!"
    assert peer.wiff(gram)  # base2
    echo = (gram, "beta")
    peer.echos.append(echo)

    peer.serviceReceives(echoic=True)
    assert not peer.echos
    assert len(peer.rxgs[mid]) == 2
    assert peer.counts[mid] == 2
    assert peer.sources[mid] == 'beta'
    assert peer.rxgs[mid][0] == bytearray(b'See ya later a')
    assert peer.rxgs[mid][1] == bytearray(b'lligator!')
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert peer.rxms[0] == ('See ya later alligator!', 'beta', None)
    peer.serviceRxMemos()
    assert not peer.rxms

    peer.close()
    assert peer.opened == False
    """ End Test """


def test_memoer_multiple():
    """Test Memoer class with small gram size and multiple queued memos
    """
    peer = memoing.Memoer(size=38)
    assert peer.size == 38
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc == 4
    assert peer.code == memoing.GramDex.Basic == '__'
    assert not peer.curt
    assert not peer.verific

    peer.reopen()
    assert peer.opened == True

    # send and receive multiple via echo
    peer.memoit("Hello there.", "alpha")
    peer.memoit("How ya doing?", "beta")
    assert len(peer.txms) == 2
    peer.serviceTxMemos()
    assert not peer.txms
    assert len(peer.txgs) == 4
    for m, d in peer.txgs:
        assert not peer.wiff(m)  # base64
        assert d in ("alpha", "beta")
    peer.serviceTxGrams(echoic=True)
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    assert len(peer.echos) == 4
    assert not peer.rxgs
    assert not peer.rxms
    assert not peer.counts
    assert not peer.sources

    peer.serviceReceives(echoic=True)
    assert not peer.echos
    assert len(peer.rxgs) == 2
    assert len(peer.counts) == 2
    assert len(peer.sources) == 2

    mid = list(peer.rxgs.keys())[0]
    assert peer.sources[mid] == 'alpha'
    assert peer.counts[mid] == 2
    assert len(peer.rxgs[mid]) == 2
    assert peer.rxgs[mid][0] == bytearray(b'Hello ')
    assert peer.rxgs[mid][1] == bytearray(b'there.')

    mid = list(peer.rxgs.keys())[1]
    assert peer.sources[mid] == 'beta'
    assert peer.counts[mid] == 2
    assert len(peer.rxgs[mid]) == 2
    assert peer.rxgs[mid][0] == bytearray(b'How ya')
    assert peer.rxgs[mid][1] == bytearray(b' doing?')

    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert len(peer.rxms) == 2
    assert peer.rxms[0] == ('Hello there.', 'alpha', None)
    assert peer.rxms[1] == ('How ya doing?', 'beta', None)
    peer.serviceRxMemos()
    assert not peer.rxms


    peer.close()
    assert peer.opened == False
    """ End Test """

def test_memoer_basic_signed():
    """Test Memoer class basic signed code
    """
    peer = memoing.Memoer(code=GramDex.Signed)
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc == 4
    assert peer.code == memoing.GramDex.Signed == '_-'
    assert not peer.curt
    # (code, mid, vid, sig, neck, head) part sizes
    assert peer.Sizes[peer.code] == (2, 22, 44, 88, 4, 160)  # cs ms vs ss ns hs
    assert peer.size == peer.MaxGramSize
    assert not peer.verific

    peer.reopen()
    assert peer.opened == True

    assert not peer.txms
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    peer.service()
    assert peer.txbs == (b'', None)

    memo = "Hello There"
    dst = "beta"
    vid = 'BKxy2sgzfplyr-tgwIxS19f2OchFHtLwPWD3v4oYimBx'
    peer.memoit(memo, dst, vid)
    assert peer.txms[0] == ('Hello There', 'beta', vid)
    peer.serviceTxMemos()
    assert not peer.txms
    g, d = peer.txgs[0]
    assert not peer.wiff(g)  # base64
    assert g.find(memo.encode()) != -1
    assert len(g) == 160 + 4 + len(memo)
    assert g[:2].decode() == GramDex.Signed
    assert d == dst == 'beta'
    peer.serviceTxGrams()
    assert not peer.txgs
    assert peer.txbs == (b'', None)

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms
    mid = '_-ALBI68S1ZIxqwFOSWFF1L2'

    sig = ('A' * 88)
    gram = (mid + vid + 'AAAA' + 'AAAB' + "Hello There" + sig).encode()
    echo = (gram, "beta")
    peer.echos.append(echo)
    peer.serviceReceives(echoic=True)
    assert peer.rxgs[mid][0] == bytearray(b'Hello There')
    assert peer.counts[mid] == 1
    assert peer.sources[mid] == 'beta'
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert peer.rxms[0] == ('Hello There', 'beta', vid)
    peer.serviceRxMemos()
    assert not peer.rxms

    # send and receive via echo
    memo = "See ya later!"
    dst = "beta"
    vid = 'BKxy2sgzfplyr-tgwIxS19f2OchFHtLwPWD3v4oYimBx'
    peer.memoit(memo, dst, vid)
    assert peer.txms[0] == ('See ya later!', 'beta', vid)
    peer.serviceTxMemos()
    assert not peer.txms
    g, d = peer.txgs[0]
    assert not peer.wiff(g)  # base64
    assert g.find(memo.encode()) != -1
    assert len(g) == 160 + 4 + len(memo)
    assert g[:2].decode() == GramDex.Signed
    assert d == dst == 'beta'
    peer.serviceTxGrams(echoic=True)
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    assert peer.echos

    assert not peer.rxgs
    assert not peer.rxms
    assert not peer.counts
    assert not peer.sources
    peer.serviceReceives(echoic=True)
    mid = list(peer.rxgs.keys())[0]
    assert peer.rxgs[mid][0] == b'See ya later!'
    assert peer.counts[mid] == 1
    assert peer.sources[mid] == 'beta'
    assert not peer.echos
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    peer.rxms[0]
    assert peer.rxms[0] == ('See ya later!', 'beta', vid)
    peer.serviceRxMemos()
    assert not peer.rxms

    # test binary q2 encoding of transmission gram header
    peer.curt = True  # set to binary base2
    memo = "Hello There"
    dst = "beta"
    vid = 'BKxy2sgzfplyr-tgwIxS19f2OchFHtLwPWD3v4oYimBx'
    peer.memoit(memo, dst, vid)
    assert peer.txms[0] == ('Hello There', 'beta', vid)
    peer.serviceTxMemos()
    assert not peer.txms
    g, d = peer.txgs[0]
    assert peer.wiff(g)  # base64
    assert g.find(memo.encode()) != -1
    assert len(g) == 3 * (160 + 4) // 4 + len(memo)
    assert helping.codeB2ToB64(g, 2) == GramDex.Signed
    assert d == dst == 'beta'
    peer.serviceTxGrams()
    assert not peer.txgs
    assert peer.txbs == (b'', None)

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms
    mid = '_-ALBI68S1ZIxqwFOSWFF1L2'
    vid = 'BKxy2sgzfplyr-tgwIxS19f2OchFHtLwPWD3v4oYimBx'
    sig = ('A' * 88)
    head = decodeB64((mid + vid + 'AAAA' + 'AAAB').encode())
    tail = decodeB64(sig.encode())
    gram = head + memo.encode() + tail
    assert peer.wiff(gram)  # base2
    assert len(gram) == 3 * (160 + 4) // 4 + len(memo)
    echo = (gram, "beta")
    peer.echos.append(echo)
    peer.serviceReceives(echoic=True)
    assert peer.rxgs[mid][0] == bytearray(b'Hello There')
    assert peer.counts[mid] == 1
    assert peer.sources[mid] == 'beta'
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert peer.rxms[0] == ('Hello There', 'beta', vid)
    peer.serviceRxMemos()
    assert not peer.rxms

    peer.close()
    assert peer.opened == False
    """ End Test """

def test_memoer_multiple_signed():
    """Test Memoer class with small gram size and multiple queued memos signed
    """
    peer = memoing.Memoer(code=GramDex.Signed, size=170)
    assert peer.size == 170
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc == 4
    assert peer.code == memoing.GramDex.Signed == '_-'
    assert not peer.curt
    assert not peer.verific

    peer.reopen()
    assert peer.opened == True

    # send and receive multiple via echo
    vid = 'BKxy2sgzfplyr-tgwIxS19f2OchFHtLwPWD3v4oYimBx'
    peer.memoit("Hello there.", "alpha", vid)
    peer.memoit("How ya doing?", "beta", vid)
    assert len(peer.txms) == 2
    peer.serviceTxMemos()
    assert not peer.txms
    assert len(peer.txgs) == 4
    for g, d in peer.txgs:
        assert not peer.wiff(g)  # base64
        assert d in ("alpha", "beta")
    peer.serviceTxGrams(echoic=True)
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    assert len(peer.echos) == 4
    assert not peer.rxgs
    assert not peer.rxms
    assert not peer.counts
    assert not peer.sources

    peer.serviceReceives(echoic=True)
    assert not peer.echos
    assert len(peer.rxgs) == 2
    assert len(peer.counts) == 2
    assert len(peer.sources) == 2

    mid = list(peer.rxgs.keys())[0]
    assert peer.sources[mid] == 'alpha'
    assert peer.counts[mid] == 2
    assert len(peer.rxgs[mid]) == 2
    assert peer.rxgs[mid][0] == bytearray(b'Hello ')
    assert peer.rxgs[mid][1] == bytearray(b'there.')

    mid = list(peer.rxgs.keys())[1]
    assert peer.sources[mid] == 'beta'
    assert peer.counts[mid] == 2
    assert len(peer.rxgs[mid]) == 2
    assert peer.rxgs[mid][0] == bytearray(b'How ya')
    assert peer.rxgs[mid][1] == bytearray(b' doing?')

    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert len(peer.rxms) == 2
    assert peer.rxms[0] == ('Hello there.', 'alpha', vid)
    assert peer.rxms[1] == ('How ya doing?', 'beta', vid)
    peer.serviceRxMemos()
    assert not peer.rxms

    # test in base2 mode
    peer.curt = True
    assert peer.curt
    peer.size = 129
    assert peer.size == 129

    # send and receive multiple via echo
    vid = 'BKxy2sgzfplyr-tgwIxS19f2OchFHtLwPWD3v4oYimBx'
    peer.memoit("Hello there.", "alpha", vid)
    peer.memoit("How ya doing?", "beta", vid)
    assert len(peer.txms) == 2
    peer.serviceTxMemos()
    assert not peer.txms
    assert len(peer.txgs) == 4
    for g, d in peer.txgs:
        assert peer.wiff(g)  # base64
        assert d in ("alpha", "beta")
    peer.serviceTxGrams(echoic=True)
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    assert len(peer.echos) == 4
    assert not peer.rxgs
    assert not peer.rxms
    assert not peer.counts
    assert not peer.sources

    peer.serviceReceives(echoic=True)
    assert not peer.echos
    assert len(peer.rxgs) == 2
    assert len(peer.counts) == 2
    assert len(peer.sources) == 2

    mid = list(peer.rxgs.keys())[0]
    assert peer.sources[mid] == 'alpha'
    assert peer.counts[mid] == 2
    assert len(peer.rxgs[mid]) == 2
    assert peer.rxgs[mid][0] == bytearray(b'Hello ')
    assert peer.rxgs[mid][1] == bytearray(b'there.')

    mid = list(peer.rxgs.keys())[1]
    assert peer.sources[mid] == 'beta'
    assert peer.counts[mid] == 2
    assert len(peer.rxgs[mid]) == 2
    assert peer.rxgs[mid][0] == bytearray(b'How ya')
    assert peer.rxgs[mid][1] == bytearray(b' doing?')

    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert len(peer.rxms) == 2
    assert peer.rxms[0] == ('Hello there.', 'alpha', vid)
    assert peer.rxms[1] == ('How ya doing?', 'beta', vid)
    peer.serviceRxMemos()
    assert not peer.rxms


    peer.close()
    assert peer.opened == False
    """ End Test """


def test_memoer_verific():
    """Test Memoer class with verific (signed required)
    """
    peer = memoing.Memoer(verific=True)
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.bc == 4
    assert peer.code == memoing.GramDex.Basic == '__'
    assert not peer.curt
    # (code, mid, vid, sig, neck, head) part sizes
    assert peer.Sizes[peer.code] == (2, 22, 0, 0, 4, 28)  # cs ms vs ss ns hs
    assert peer.size == peer.MaxGramSize
    assert peer.verific

    peer.reopen()
    assert peer.opened == True

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms
    mid = '__ALBI68S1ZIxqwFOSWFF1L2'  # not signed code
    gram = (mid + 'AAAA' + 'AAAB' + "Hello There").encode()
    echo = (gram, "beta")
    peer.echos.append(echo)
    peer.serviceReceives(echoic=True)
    assert not peer.rxgs  # dropped gram
    assert not peer.echos
    assert not peer.rxms

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms
    mid = '_-ALBI68S1ZIxqwFOSWFF1L2'
    vid = 'BKxy2sgzfplyr-tgwIxS19f2OchFHtLwPWD3v4oYimBx'
    sig = ('A' * 88)
    gram = (mid + vid + 'AAAA' + 'AAAB' + "Hello There" + sig).encode()
    echo = (gram, "beta")
    peer.echos.append(echo)
    peer.serviceReceives(echoic=True)
    assert peer.rxgs[mid][0] == bytearray(b'Hello There')
    assert peer.counts[mid] == 1
    assert peer.sources[mid] == 'beta'
    assert not peer.echos
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert peer.rxms[0] == ('Hello There', 'beta', vid)
    peer.serviceRxMemos()
    assert not peer.rxms

    peer.close()
    assert peer.opened == False
    """ End Test """


def test_open_memoer():
    """Test contextmanager decorator openMemoer
    """
    with (memoing.openMemoer(name='zeta') as zeta):

        assert zeta.opened
        assert zeta.name == 'zeta'


    assert not zeta.opened

    """ End Test """


def test_memoer_doer():
    """Test MemoerDoer class
    """
    tock = 0.03125
    ticks = 4
    limit = ticks *  tock
    doist = doing.Doist(tock=tock, real=True, limit=limit)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == tock == 0.03125
    assert doist.real == True
    assert doist.limit == limit == 0.125
    assert doist.doers == []

    peer = memoing.Memoer()

    mgdoer = memoing.MemoerDoer(peer=peer)
    assert mgdoer.peer == peer
    assert not mgdoer.peer.opened
    assert mgdoer.tock == 0.0  # ASAP

    doers = [mgdoer]
    doist.do(doers=doers)
    assert doist.tyme == limit
    assert mgdoer.peer.opened == False

    """End Test """

def test_tymee_memoer_basic():
    """Test TymeeMemoer class basic
    """
    peer = memoing.TymeeMemoer()
    assert peer.tymeout == 0.0
    assert peer.name == "main"
    assert peer.opened == False
    assert peer.code == memoing.GramDex.Basic == '__'
    assert not peer.curt
    # (code, mid, vid, neck, head, sig) part sizes
    assert peer.Sizes[peer.code] == (2, 22, 0, 0, 4, 28)  # cs ms vs ss ns hs
    assert peer.size == peer.MaxGramSize
    assert not peer.verific

    peer.reopen()
    assert peer.opened == True

    assert not peer.txms
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    peer.service()
    assert peer.txbs == (b'', None)

    memo = "Hello There"
    dst = "beta"
    peer.memoit(memo, dst)
    assert peer.txms[0] == ('Hello There', 'beta', None)
    peer.serviceTxMemos()
    assert not peer.txms
    m, d = peer.txgs[0]
    assert not peer.wiff(m)  # base64
    assert m.endswith(memo.encode())
    assert d == dst == 'beta'
    peer.serviceTxGrams()
    assert not peer.txgs
    assert peer.txbs == (b'', None)

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms
    mid = '__ALBI68S1ZIxqwFOSWFF1L2'
    gram = (mid + 'AAAA' + 'AAAB' + "Hello There").encode()
    echo = (gram, "beta")
    peer.echos.append(echo)
    peer.serviceReceives(echoic=True)
    assert peer.rxgs[mid][0] == bytearray(b'Hello There')
    assert peer.counts[mid] == 1
    assert peer.sources[mid] == 'beta'
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert peer.rxms[0] == ('Hello There', 'beta', None)
    peer.serviceRxMemos()
    assert not peer.rxms

    # send and receive via echo
    memo = "See ya later!"
    dst = "beta"
    peer.memoit(memo, dst)
    assert peer.txms[0] == ('See ya later!', 'beta', None)
    peer.serviceTxMemos()
    assert not peer.txms
    m, d = peer.txgs[0]
    assert not peer.wiff(m)   # base64
    assert m.endswith(memo.encode())
    assert d == dst == 'beta'
    peer.serviceTxGrams(echoic=True)
    assert not peer.txgs
    assert peer.txbs == (b'', None)
    assert peer.echos

    assert not peer.rxgs
    assert not peer.rxms
    assert not peer.counts
    assert not peer.sources
    peer.serviceReceives(echoic=True)
    mid = list(peer.rxgs.keys())[0]
    assert peer.rxgs[mid][0] == b'See ya later!'
    assert peer.counts[mid] == 1
    assert peer.sources[mid] == 'beta'
    assert not peer.echos
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    peer.rxms[0]
    assert peer.rxms[0] == ('See ya later!', 'beta', None)
    peer.serviceRxMemos()
    assert not peer.rxms

    # test binary q2 encoding of transmission gram header
    peer.curt = True  # set to binary base2
    memo = "Hello There"
    dst = "beta"
    peer.memoit(memo, dst)
    assert peer.txms[0] == ('Hello There', 'beta', None)
    peer.serviceTxMemos()
    assert not peer.txms
    m, d = peer.txgs[0]
    assert peer.wiff(m)   # base2
    assert m.endswith(memo.encode())
    assert d == dst == 'beta'
    peer.serviceTxGrams()
    assert not peer.txgs
    assert peer.txbs == (b'', None)

    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert not peer.rxms
    mid = '__ALBI68S1ZIxqwFOSWFF1L2'
    headneck = decodeB64((mid + 'AAAA' + 'AAAB').encode())
    gram = headneck + b"Hello There"
    assert peer.wiff(gram)   # base2
    echo = (gram, "beta")
    peer.echos.append(echo)
    peer.serviceReceives(echoic=True)
    assert peer.rxgs[mid][0] == bytearray(b'Hello There')
    assert peer.counts[mid] == 1
    assert peer.sources[mid] == 'beta'
    peer.serviceRxGrams()
    assert not peer.rxgs
    assert not peer.counts
    assert not peer.sources
    assert peer.rxms[0] == ('Hello There', 'beta', None)
    peer.serviceRxMemos()
    assert not peer.rxms

    # Test wind
    tymist = tyming.Tymist(tock=1.0)
    peer.wind(tymth=tymist.tymen())
    assert peer.tyme == tymist.tyme == 0.0
    tymist.tick()
    assert peer.tyme == tymist.tyme == 1.0

    peer.close()
    assert peer.opened == False
    """ End Test """


def test_open_tm():
    """Test contextmanager decorator openTM for openTymeeMemoer
    """
    with (memoing.openTM(name='zeta') as zeta):

        assert zeta.opened
        assert zeta.name == 'zeta'
        assert zeta.tymeout == 0.0


    assert not zeta.opened

    """ End Test """


def test_tymee_memoer_doer():
    """Test TymeeMemoerDoer class
    """
    tock = 0.03125
    ticks = 4
    limit = ticks *  tock
    doist = doing.Doist(tock=tock, real=True, limit=limit)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == tock == 0.03125
    assert doist.real == True
    assert doist.limit == limit == 0.125
    assert doist.doers == []

    peer = memoing.TymeeMemoer()

    tmgdoer = memoing.TymeeMemoerDoer(peer=peer)
    assert tmgdoer.peer == peer
    assert not tmgdoer.peer.opened
    assert tmgdoer.tock == 0.0  # ASAP

    doers = [tmgdoer]
    doist.do(doers=doers)
    assert doist.tyme == limit
    assert tmgdoer.peer.opened == False

    tymist = tyming.Tymist(tock=1.0)
    tmgdoer.wind(tymth=tymist.tymen())
    assert tmgdoer.tyme == tymist.tyme == 0.0
    assert peer.tyme == tymist.tyme == 0.0
    tymist.tick()
    assert tmgdoer.tyme == tymist.tyme == 1.0
    assert peer.tyme == tymist.tyme == 1.0

    """End Test """



if __name__ == "__main__":
    test_memoer_class()
    test_memoer_basic()
    test_memoer_small_gram_size()
    test_memoer_multiple()
    test_memoer_basic_signed()
    test_memoer_multiple_signed()
    test_memoer_verific()
    test_open_memoer()
    test_memoer_doer()
    test_tymee_memoer_basic()
    test_open_tm()
    test_tymee_memoer_doer()

