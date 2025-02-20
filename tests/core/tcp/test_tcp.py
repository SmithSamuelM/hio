# -*- encoding: utf-8 -*-
"""
tests.core.test_tcp module

"""
import pytest

import sys
import os
import time
import socket
from collections import deque
import ssl

from hio.base import tyming, doing
from hio.core import tcp

def test_tcp_basic():
    """
    Test the tcp connection between client and server

    client send from and receive to port is ephemeral
    server receive to and send from port is well known

    Server listens on ist well know  receive to and send from port

    So incoming to server.
        Source address is client host and client ephemeral port
        Destination address is server host and server well known port

    Each accept socket on server is a different duple of client source, server dest
        all the dest are the same but each source is differenct so can route
        based on the source.

    Server routes incoming packets to accept socket port. The routing uses
           the clients send from ephemeral port to do the routing to the
           correct accept socket. All the accept sockets have the same local
           port but a different remote IP host .
    The servers accept socket port is the well known port so still receives to
           and sends from its well know port.
    The server sends to and receives from the clients ephemeral port number.


    """
    tymist = tyming.Tymist()
    client = tcp.Client(tymth=tymist.tymen())
    assert client.tymeout == 0.0
    assert isinstance(client.tymer, tyming.Tymer)
    assert client.tymer.duration == client.tymeout

    assert client.ha == ('127.0.0.1', 56000)
    assert (client.host, client.port) == client.ha
    assert client.hostname == client.host
    assert client.cs == None
    assert client.ca == (None, None)
    assert client.accepted == False
    assert client.cutoff == False
    assert client.reconnectable == False
    assert client.opened == False

    assert client.bs == 8096
    assert isinstance(client.txbs, bytearray)
    assert isinstance(client.rxbs, bytearray)
    assert client.wl == None

    tymist = tyming.Tymist()
    with tcp.openClient(tymth=tymist.tymen(), tymeout=0.5) as client:
        assert client.tymeout == 0.5
        assert client.ha == ('127.0.0.1', 56000)
        assert client.opened == True
        assert client.accepted == False
        assert client.cutoff == False
        assert client.reconnectable == False


    assert client.opened == False
    assert client.accepted == False
    assert client.cutoff == False

    server = tcp.Server()
    assert server.tymeout == 1.0

    assert server.ha == ('', 56000)
    assert server.eha == ('127.0.0.1', 56000)
    assert server.opened == False

    assert server.bs == 8096
    assert isinstance(server.axes, deque)
    assert isinstance(server.ixes, dict)
    assert server.wl == None

    with tcp.openServer(tymth=tymist.tymen(), tymeout=1.5) as server:
        assert server.ha == ('0.0.0.0', 56000)
        assert server.eha == ('127.0.0.1', 56000)
        assert server.opened == True

    assert server.opened == False

    tymist = tyming.Tymist()
    with tcp.openServer(tymth=tymist.tymen(), ha=("", 6101)) as server, \
         tcp.openClient(tymth=tymist.tymen(), ha=("127.0.0.1", 6101)) as beta, \
         tcp.openClient(tymth=tymist.tymen(), ha=("127.0.0.1", 6101)) as gamma:

        assert server.opened == True
        assert beta.opened == True
        assert gamma.opened == True

        assert server.ha == ('0.0.0.0', 6101)  # listen interface
        assert server.eha == ('127.0.0.1', 6101)  # normalized listen/accept external interface
        assert beta.ha == ('127.0.0.1', 6101)  # server listen/accept maybe sha  (server host address)

        assert beta.accepted == False
        assert beta.connected == False
        assert beta.cutoff == False

        assert gamma.accepted == False
        assert gamma.connected == False
        assert gamma.cutoff == False

        #  connect beta to server
        while not (beta.connected and beta.ca in server.ixes):
            beta.serviceConnect()
            server.serviceConnects()
            time.sleep(0.05)

        assert beta.accepted == True
        assert beta.connected == True
        assert beta.cutoff == False
        assert beta.ca == beta.cs.getsockname()  # local connection address
        assert beta.ha == beta.cs.getpeername()  # remote connection address
        assert server.eha == beta.ha  # server external, beta external for server

        ixBeta = server.ixes[beta.ca]
        assert ixBeta.cs.getsockname() == beta.cs.getpeername()  # ixBeta local beta remote
        assert ixBeta.cs.getpeername() == beta.cs.getsockname()  # ixBeta remote beta local
        assert ixBeta.ca == beta.ca == ixBeta.cs.getpeername()
        assert ixBeta.ha == beta.ha == ixBeta.cs.getsockname()

        msgOut = b"Beta sends to Server"
        count = beta.send(msgOut)
        assert count == len(msgOut)
        time.sleep(0.05)
        msgIn = ixBeta.receive()
        assert msgOut == msgIn

        # receive without sending
        msgIn = ixBeta.receive()
        assert msgIn is None

        # send multiple
        msgOut1 = b"First Message"
        count = beta.send(msgOut1)
        assert count == len(msgOut1)
        msgOut2 = b"Second Message"
        count = beta.send(msgOut2)
        assert count == len(msgOut2)
        time.sleep(0.05)
        msgIn  = ixBeta.receive()
        assert msgIn == msgOut1 + msgOut2

        # send from server to beta
        msgOut = b"Server sends to Beta"
        count = ixBeta.send(msgOut)
        assert count == len(msgOut)
        time.sleep(0.05)
        msgIn = beta.receive()
        assert msgOut == msgIn

        # receive without sending
        msgIn = beta.receive()
        assert msgIn is None

        # build message too big to fit in buffer
        size = beta.actualBufSizes()[0]
        msgOut = bytearray()
        count = 0
        while (len(msgOut) <= size * 4):
            msgOut.extend(b"%032x_" %  (count))  #  need to fix this
            count += 1
        assert len(msgOut) >= size * 4

        msgIn = bytearray()
        txbs = bytearray(msgOut)  # make copy
        size = 0
        while len(msgIn) < len(msgOut):
            #if size < len(msgOut):
                #size += beta.send(msgOut[size:])
            count = beta.send(txbs)
            del txbs[:count]
            size += count
            time.sleep(0.05)
            msgIn.extend(ixBeta.receive())
        assert size == len(msgOut)
        assert msgOut == msgIn

        #  gamma to server
        while not (gamma.connected and gamma.ca in server.ixes):
            gamma.serviceConnect()
            server.serviceConnects()
            time.sleep(0.05)

        assert gamma.accepted == True
        assert gamma.connected == True
        assert gamma.cutoff == False
        assert gamma.ca == gamma.cs.getsockname()
        assert gamma.ha == gamma.cs.getpeername()
        assert server.eha, gamma.ha
        ixGamma = server.ixes[gamma.ca]
        assert ixGamma.cs.getsockname() == gamma.cs.getpeername()
        assert ixGamma.cs.getpeername() == gamma.cs.getsockname()
        assert ixGamma.ca == gamma.ca
        assert ixGamma.ha == gamma.ha

        msgOut = b"Gamma sends to Server"
        count = gamma.send(msgOut)
        assert count == len(msgOut)
        time.sleep(0.05)
        msgIn = ixGamma.receive()
        assert msgOut == msgIn

        # receive without sending
        msgIn = ixGamma.receive()
        assert msgIn is None

        # send from server to gamma
        msgOut = b"Server sends to Gamma"
        count = ixGamma.send(msgOut)
        assert count == len(msgOut)
        time.sleep(0.05)
        msgIn = gamma.receive()
        assert msgOut == msgIn

        # recieve without sending
        msgIn = gamma.receive()
        assert msgIn is None

        # close beta and then attempt to send
        beta.close()
        msgOut = b"Beta send on closed socket"
        with pytest.raises(AttributeError):
            count = beta.send(msgOut)

        # attempt to receive on closed socket
        with pytest.raises(AttributeError):
            msgIn = beta.receive()

        # read on server after closed beta
        msgIn = ixBeta.receive()
        assert msgIn == b''

        # send on server after closed beta
        msgOut = b"Servers sends to Beta after close"
        count = ixBeta.send(msgOut)
        assert count == len(msgOut) #apparently works

        # close ixBeta manually
        ixBeta.close()
        del server.ixes[ixBeta.ca]
        time.sleep(0.05)
        #after close no socket .cs so can't receive
        with pytest.raises(AttributeError):
             msgIn = ixBeta.receive()
        assert ixBeta.cutoff == True

        # send on gamma to servver first then shutdown gamma sends
        msgOut = b"Gamma sends to server"
        count = gamma.send(msgOut)
        assert count == len(msgOut)
        gamma.shutdownSend()
        time.sleep(0.05)
        msgIn = ixGamma.receive()
        assert msgOut ==  msgIn   # send before shutdown worked
        msgIn = ixGamma.receive()
        assert msgIn == b''  # gamma shutdown detected, not None
        assert ixGamma.cutoff == True

        # send from server to gamma first  then shutdown server send
        msgOut = b"Server sends to Gamma"
        count = ixGamma.send(msgOut)
        assert count ==  len(msgOut)
        ixGamma.shutdown()  # shutdown server connection to gamma
        time.sleep(0.05)
        msgIn = gamma.receive()
        assert msgOut == msgIn
        msgIn = gamma.receive()
        if 'linux' or 'windows' in sys.platform:
            assert msgIn ==  b''  # server shutdown detected not None
            assert gamma.cutoff == True
        else:
            assert msgIn == None  # server shutdown not detected
            assert gamma.cutoff == False
        time.sleep(0.05)
        msgIn = gamma.receive()
        if 'linux' or 'windows' in sys.platform:
            assert msgIn == b''  # server shutdown detected not None
            assert gamma.cutoff == True
        else:
            assert msgIn == None   # server shutdown not detected
            assert gamma.cutoff == False

        ixGamma.close()  # close server connection to gamma
        del server.ixes[ixGamma.ca]
        time.sleep(0.05)
        msgIn = gamma.receive()
        assert msgIn == b''  # server close is detected
        assert gamma.cutoff == True

        # reopen beta
        assert beta.reopen() == True
        assert beta.accepted == False
        assert beta.connected == False
        assert beta.cutoff == False

        # reconnect beta to server
        while  not (beta.connected and beta.ca in server.ixes):
            beta.serviceConnect()
            server.serviceConnects()
            time.sleep(0.05)

        assert beta.accepted == True
        assert beta.connected == True
        assert beta.cutoff == False
        assert beta.ca == beta.cs.getsockname()
        assert beta.ha == beta.cs.getpeername()
        assert server.eha == beta.ha

        ixBeta = server.ixes[beta.ca]
        assert ixBeta.cs.getsockname() == beta.cs.getpeername()
        assert ixBeta.cs.getpeername() == beta.cs.getsockname()
        assert ixBeta.ca == beta.ca
        assert ixBeta.ha == beta.ha

        msgOut = b"Beta sends to server"
        count = beta.send(msgOut)
        assert count == len(msgOut)
        time.sleep(0.05)
        msgIn = ixBeta.receive()
        assert msgOut == msgIn

        # send from server to beta
        msgOut = b"Server sends to Beta"
        count = ixBeta.send(msgOut)
        assert count == len(msgOut)
        time.sleep(0.05)
        msgIn = beta.receive()
        assert msgOut == msgIn

        # send from server to beta then shutdown sever and attempt to send again
        msgOut1 = b"Server sends to Beta"
        count = ixBeta.send(msgOut)
        assert count == len(msgOut1)
        ixBeta.shutdownSend()
        msgOut2 = b"Server send again after server shutdowns socket"
        with pytest.raises(OSError) as ex:
            count = ixBeta.send(msgOut)
        assert ex.typename == 'BrokenPipeError'
        time.sleep(0.05)
        msgIn = beta.receive()
        assert msgOut1 == msgIn
        msgIn = beta.receive()
        assert msgIn == b''  # beta detects shutdown socket
        assert beta.cutoff == True

        # send from beta to server then shutdown beta
        msgOut = b"Beta sends to server"
        count = beta.send(msgOut)
        assert count == len(msgOut)
        beta.shutdown()
        time.sleep(0.05)
        msgIn = ixBeta.receive()
        assert msgOut == msgIn
        time.sleep(0.05)
        msgIn = ixBeta.receive()
        if 'linux' or 'windows' in sys.platform:
            assert ixBeta.cutoff == True
            assert msgIn == b''  # server does detect shutdown
        else:
            assert ixBeta.cutoff == False
            assert  msgIn == None  # server does not detect shutdown
        beta.close()
        time.sleep(0.05)
        msgIn = ixBeta.receive()
        assert msgIn == b''  # server detects closed socket
        ixBeta.close()
        del server.ixes[ixBeta.ca]

        # reopen gamma
        assert gamma.reopen() == True
        assert gamma.accepted == False
        assert gamma.connected == False
        assert gamma.cutoff == False
        # reconnect gamma to server
        while not (gamma.connected and gamma.ca in server.ixes):
            gamma.serviceConnect()
            server.serviceConnects()
            time.sleep(0.05)

        assert gamma.accepted == True
        assert gamma.connected == True
        assert gamma.cutoff == False
        assert gamma.ca == gamma.cs.getsockname()
        assert gamma.ha == gamma.cs.getpeername()
        assert server.eha == gamma.ha

        ixGamma = server.ixes[gamma.ca]
        assert ixGamma.cs.getsockname() == gamma.cs.getpeername()
        assert ixGamma.cs.getpeername() == gamma.cs.getsockname()
        assert ixGamma.ca == gamma.ca
        assert ixGamma.ha == gamma.ha

        msgOut = b"Gamma sends to server"
        count = gamma.send(msgOut)
        assert count == len(msgOut)
        time.sleep(0.05)
        msgIn = ixGamma.receive()
        assert msgOut == msgIn

        # close both sides and reopen Gamma
        gamma.close()
        time.sleep(0.05)
        msgIn = ixGamma.receive()
        assert ixGamma.cutoff ==True  # closed on other end
        assert msgIn == b''  # server detects close
        ixGamma.close()
        del server.ixes[ixGamma.ca]

        # reopen gamma
        assert gamma.reopen() == True
        assert gamma.accepted == False
        assert gamma.connected == False
        assert gamma.cutoff == False

        # reconnect gamma to server
        while not (gamma.connected and gamma.ca in server.ixes):
            gamma.serviceConnect()
            server.serviceConnects()
            time.sleep(0.05)

        assert gamma.accepted == True
        assert gamma.connected == True
        assert gamma.cutoff == False
        assert gamma.ca == gamma.cs.getsockname()
        assert gamma.ha == gamma.cs.getpeername()
        assert server.eha == gamma.ha

        ixGamma = server.ixes[gamma.ca]
        assert ixGamma.cs.getsockname() == gamma.cs.getpeername()
        assert ixGamma.cs.getpeername() == gamma.cs.getsockname()
        assert ixGamma.ca == gamma.ca
        assert ixGamma.ha == gamma.ha

        # send from server to gamma
        msgOut = b"Server sends to Gamma"
        count = ixGamma.send(msgOut)
        assert count == len(msgOut)
        time.sleep(0.05)
        msgIn = gamma.receive()
        assert msgOut == msgIn

        ixGamma.close()
        del server.ixes[ixGamma.ca]
        time.sleep(0.05)
        msgIn = gamma.receive()
        assert msgIn == b''  # gamma detects close
        assert gamma.cutoff == True


    assert beta.opened == False
    assert gamma.opened == False
    assert server.opened == False

    """Done Test"""

def test_tcp_service():
    """
    Test Classes tcp service methods
    """
    tymist = tyming.Tymist()
    with tcp.openServer(tymth=tymist.tymen(),  ha=("", 6101)) as server, \
         tcp.openClient(tymth=tymist.tymen(),  ha=("127.0.0.1", 6101)) as beta:

        assert server.opened == True
        assert server.ha == ('0.0.0.0', 6101)
        assert server.eha == ('127.0.0.1', 6101)

        assert beta.opened == True
        assert beta.accepted == False
        assert beta.connected == False
        assert beta.cutoff == False

        # connect beta to server
        while not (beta.connected and beta.ca in server.ixes):
            beta.serviceConnect()
            server.serviceConnects()
            time.sleep(0.05)

        assert beta.accepted == True
        assert beta.connected == True
        assert beta.cutoff == False
        assert beta.ca == beta.cs.getsockname()
        assert beta.ha == beta.cs.getpeername() == server.eha

        ixBeta = server.ixes[beta.ca]
        assert ixBeta.cs.getsockname() == beta.cs.getpeername()
        assert ixBeta.cs.getpeername() == beta.cs.getsockname()
        assert ixBeta.ca == beta.ca
        assert ixBeta.ha == beta.ha

        msgOut1 = b"Beta sends to Server first"
        beta.tx(msgOut1)
        while not ixBeta.rxbs and beta.txbs:
            beta.serviceSends()
            time.sleep(0.05)
            server.serviceReceivesAllIx()
            time.sleep(0.05)
        msgIn = bytes(ixBeta.rxbs)
        assert msgIn == msgOut1
        offset = len(ixBeta.rxbs)  # offset into .rxbs of first message

        # send multiple additional messages
        msgOut2 = b"Beta sends to Server second"
        beta.tx(msgOut2)
        msgOut3 = b"Beta sends to Server third"
        beta.tx(msgOut3)
        while len(ixBeta.rxbs) < len(msgOut1) + len(msgOut2) + len(msgOut3):
            beta.serviceSends()
            server.serviceReceivesAllIx()
            time.sleep(0.05)
        msgIn = bytes(ixBeta.rxbs)
        assert msgIn == msgOut1 + msgOut2 + msgOut3
        ixBeta.clearRxbs()  # clear out the receive buffer

        # build message too big to fit in buffer
        size = beta.actualBufSizes()[0]
        msgOutBig = bytearray()
        count = 0
        while (len(msgOutBig) <= size * 4):
            msgOutBig.extend(b"%032x_" % (count))
            count += 1
        assert len(msgOutBig) >= size * 4

        beta.tx(msgOutBig)
        while len(ixBeta.rxbs) < len(msgOutBig):
            beta.serviceSends()
            time.sleep(0.05)
            server.serviceReceivesAllIx()
            time.sleep(0.05)
        msgIn = bytes(ixBeta.rxbs)
        ixBeta.clearRxbs()
        assert msgIn == msgOutBig

        # send from server to beta
        msgOut = b"Server sends to Beta"
        ixBeta.tx(msgOut)
        while len(beta.rxbs) < len(msgOut):
            server.serviceSendsAllIx()
            beta.serviceReceives()
            time.sleep(0.05)
        msgIn = bytes(beta.rxbs)
        beta.clearRxbs()
        assert msgIn == msgOut

        # send big from server to beta
        ixBeta.tx(msgOutBig)
        while len(beta.rxbs) < len(msgOutBig):
            server.serviceSendsAllIx()
            time.sleep(0.05)
            beta.serviceReceives()
            time.sleep(0.05)
        msgIn = bytes(beta.rxbs)
        beta.clearRxbs()
        assert msgIn == msgOutBig

    assert beta.opened == False
    assert server.opened == False

    """Done Test"""

def test_client_auto_reconnect():
    """
    Test client auto reconnect when  .reconnectable
    """
    tymist = tyming.Tymist(tock=0.05)
    with tcp.openServer(tymth=tymist.tymen(), ha=("", 6101)) as server, \
         tcp.openClient(tymth=tymist.tymen(), tymeout=0.2, reconnectable=True,
                    ha=("127.0.0.1", 6101)) as beta:

        # close server
        server.close()
        assert server.opened == False

        assert beta.opened == True
        assert beta.accepted == False
        assert beta.connected == False
        assert beta.cutoff == False
        assert beta.reconnectable == True

        # attempt to connect beta to serve while server down (closed)
        while tymist.tyme <= 0.25:
            beta.serviceConnect()
            tymist.tick()
            time.sleep(0.05)

        assert beta.accepted == False
        assert beta.connected == False

        assert server.reopen() == True
        assert server.ha == ('0.0.0.0', 6101)
        assert server.eha== ('127.0.0.1', 6101)

        assert beta.ha == server.eha

        # attempt to connect beta to server while server up (opened)
        while not (beta.connected and beta.ca in server.ixes):
            beta.serviceConnect()
            server.serviceConnects()
            tymist.tick()  # advances clients reconnect retry tymer
            time.sleep(0.05)

        assert beta.accepted == True
        assert beta.connected == True
        assert beta.cutoff == False
        assert beta.ca == beta.cs.getsockname()
        assert beta.ha == beta.cs.getpeername()
        assert server.eha == beta.ha

        ixBeta = server.ixes[beta.ca]
        assert ixBeta.cs.getsockname() == beta.cs.getpeername()
        assert ixBeta.cs.getpeername() == beta.cs.getsockname()
        assert ixBeta.ca == beta.ca
        assert ixBeta.ha == beta.ha

        msgOut = b"Beta sends to Server on reconnect"
        beta.tx(msgOut)
        while not ixBeta.rxbs and beta.txbs:
            beta.serviceSends()
            time.sleep(0.05)
            server.serviceReceivesAllIx()
            time.sleep(0.05)
        msgIn = bytes(ixBeta.rxbs)
        assert msgIn == msgOut
        index = len(ixBeta.rxbs)

    assert beta.opened == False
    assert server.opened == False
    """Done Test"""

def localTestCertDirPath():
    """
    Returns local testing directory path for TLS certs
    """
    localDirPath = os.path.dirname(
                    os.path.abspath(
                        sys.modules.get(__name__).__file__))
    return(os.path.join(localDirPath, 'certs'))

def  test_tcp_tls_default_context():
    """
    Test tcp connection with tls default context
    """

    certDirPath = localTestCertDirPath()
    assert os.path.exists(certDirPath)
    #serverKeypath = '/etc/pki/tls/certs/server_key.pem'  # local server private key
    #serverCertpath = '/etc/pki/tls/certs/server_cert.pem'  # local server public cert
    #clientCafilepath = '/etc/pki/tls/certs/client.pem' # remote client public cert

    #clientKeypath = '/etc/pki/tls/certs/client_key.pem'  # local client private key
    #clientCertpath = '/etc/pki/tls/certs/client_cert.pem'  # local client public cert
    #serverCafilepath = '/etc/pki/tls/certs/server.pem' # remote server public cert

    serverKeyPath = os.path.join(certDirPath, 'server_key.pem')  # local server private key
    serverCertPath = os.path.join(certDirPath, 'server_cert.pem')  # local server public cert
    clientCaPath = os.path.join(certDirPath, 'client.pem') # remote client public cert

    clientKeyPath = os.path.join(certDirPath, 'client_key.pem')  # local client private key
    clientCertPath = os.path.join(certDirPath, 'client_cert.pem')  # local client public cert
    serverCaPath = os.path.join(certDirPath, 'server.pem') # remote server public cert

    assert os.path.exists(serverKeyPath)
    assert os.path.exists(serverCertPath)
    assert os.path.exists(clientCaPath)
    assert os.path.exists(clientKeyPath)
    assert os.path.exists(clientCertPath)
    assert os.path.exists(serverCaPath)

    serverCertCommonName = 'localhost' # match hostname uses servers's cert commonname

    tymist = tyming.Tymist()
    with tcp.openServer(cls=tcp.ServerTls,
                    tymth=tymist.tymen(),
                    ha=("", 6101),
                    bs=16192,
                    keypath=serverKeyPath,
                    certpath=serverCertPath,
                    cafilepath=clientCaPath) as server, \
         tcp.openClient(cls=tcp.ClientTls,
                    tymth=tymist.tymen(),
                    ha=("127.0.0.1", 6101),
                    bs=16192,
                    certedhost=serverCertCommonName,
                    keypath=clientKeyPath,
                    certpath=clientCertPath,
                    cafilepath=serverCaPath,) as beta:

        assert server.opened == True
        assert server.eha == ('127.0.0.1', 6101)
        assert server.ha == ('0.0.0.0', 6101)

        assert beta.opened == True
        assert beta.accepted == False
        assert beta.connected == False
        assert beta.cutoff == False

        # Connect beta to server
        while not(beta.connected and len(server.ixes) >= 1):
            beta.serviceConnect()
            server.serviceConnects()
            time.sleep(0.01)

        assert beta.accepted == True
        assert beta.connected == True
        assert beta.cutoff == False
        assert beta.ca == beta.cs.getsockname()
        assert beta.ha == beta.cs.getpeername()

        ixBeta = server.ixes[beta.ca]
        assert ixBeta.cs.getsockname() == beta.cs.getpeername()
        assert ixBeta.cs.getpeername() == beta.cs.getsockname()
        assert ixBeta.ca == beta.ca
        assert ixBeta.ha == beta.ha

        msgOut = b"Beta sends to Server\n"
        beta.tx(msgOut)
        while not( not beta.txbs and ixBeta.rxbs):
            beta.serviceSends()
            server.serviceReceivesAllIx()
            time.sleep(0.01)

        time.sleep(0.05)
        server.serviceReceivesAllIx()

        msgIn = bytes(ixBeta.rxbs)
        assert msgIn == msgOut
        ixBeta.clearRxbs()

        msgOut = b'Server sends to Beta\n'
        ixBeta.tx(msgOut)
        while not (not ixBeta.txbs and beta.rxbs):
            server.serviceSendsAllIx()
            beta.serviceReceives()
            time.sleep(0.01)

        msgIn = bytes(beta.rxbs)
        assert msgIn == msgOut
        beta.clearRxbs()

    assert beta.opened == False
    assert server.opened == False
    """Done Test"""


def test_tcp_tls_verify_both():
    """
    Test TCP TLS client server connection with verify certs for both client and server
    """

    certDirPath = localTestCertDirPath()
    assert os.path.exists(certDirPath)

    serverKeyPath = os.path.join(certDirPath, 'server_key.pem')  # local server private key
    serverCertPath = os.path.join(certDirPath, 'server_cert.pem')  # local server public cert
    clientCaPath = os.path.join(certDirPath, 'client.pem') # remote client public cert

    clientKeyPath = os.path.join(certDirPath, 'client_key.pem')  # local client private key
    clientCertPath = os.path.join(certDirPath, 'client_cert.pem')  # local client public cert
    serverCaPath = os.path.join(certDirPath, 'server.pem') # remote server public cert

    assert os.path.exists(serverKeyPath)
    assert os.path.exists(serverCertPath)
    assert os.path.exists(clientCaPath)
    assert os.path.exists(clientKeyPath)
    assert os.path.exists(clientCertPath)
    assert os.path.exists(serverCaPath)

    serverCertCommonName = 'localhost' # match hostname uses servers's cert commonname

    tymist = tyming.Tymist()
    with tcp.openServer(cls=tcp.ServerTls,
                    tymth=tymist.tymen(),
                    ha=("", 6101),
                    bs=16192,
                    keypath=serverKeyPath,
                    certpath=serverCertPath,
                    cafilepath=clientCaPath,
                    certify=ssl.CERT_REQUIRED,) as server, \
         tcp.openClient(cls=tcp.ClientTls,
                    tymth=tymist.tymen(),
                    ha=("127.0.0.1", 6101),
                    bs=16192,
                    certedhost=serverCertCommonName,
                    keypath=clientKeyPath,
                    certpath=clientCertPath,
                    cafilepath=serverCaPath,
                    certify=ssl.CERT_REQUIRED,
                    hostify=True,) as beta:


        assert server.opened == True
        assert server.eha == ('127.0.0.1', 6101)
        assert server.ha == ('0.0.0.0', 6101)

        assert beta.opened == True
        assert beta.accepted == False
        assert beta.connected == False
        assert beta.cutoff == False


        # Connect beta to server
        while not(beta.connected and len(server.ixes) >= 1):
            beta.serviceConnect()
            server.serviceConnects()
            time.sleep(0.01)

        assert beta.accepted == True
        assert beta.connected == True
        assert beta.cutoff == False
        assert beta.ca == beta.cs.getsockname()
        assert beta.ha == beta.cs.getpeername()

        ixBeta = server.ixes[beta.ca]
        assert ixBeta.cs.getsockname() == beta.cs.getpeername()
        assert ixBeta.cs.getpeername() == beta.cs.getsockname()
        assert ixBeta.ca == beta.ca
        assert ixBeta.ha == beta.ha

        msgOut = b"Beta sends to Server\n"
        beta.tx(msgOut)
        while not( not beta.txbs and ixBeta.rxbs):
            beta.serviceSends()
            server.serviceReceivesAllIx()
            time.sleep(0.01)

        time.sleep(0.05)
        server.serviceReceivesAllIx()

        msgIn = bytes(ixBeta.rxbs)
        assert msgIn == msgOut
        ixBeta.clearRxbs()

        msgOut = b'Server sends to Beta\n'
        ixBeta.tx(msgOut)
        while not (not ixBeta.txbs and beta.rxbs):
            server.serviceSendsAllIx()
            beta.serviceReceives()
            time.sleep(0.01)

        msgIn = bytes(beta.rxbs)
        assert msgIn == msgOut
        beta.clearRxbs()

    assert beta.opened == False
    assert server.opened == False
    """Done Test"""


def test_tcp_tls_verify_client():
    """
    Test TCP TLS client server connection with verify certs for client not server
    """

    certDirPath = localTestCertDirPath()
    assert os.path.exists(certDirPath)

    serverKeyPath = os.path.join(certDirPath, 'server_key.pem')  # local server private key
    serverCertPath = os.path.join(certDirPath, 'server_cert.pem')  # local server public cert
    clientCaPath = os.path.join(certDirPath, 'client.pem') # remote client public cert

    clientKeyPath = os.path.join(certDirPath, 'client_key.pem')  # local client private key
    clientCertPath = os.path.join(certDirPath, 'client_cert.pem')  # local client public cert
    serverCaPath = os.path.join(certDirPath, 'server.pem') # remote server public cert

    assert os.path.exists(serverKeyPath)
    assert os.path.exists(serverCertPath)
    assert os.path.exists(clientCaPath)
    assert os.path.exists(clientKeyPath)
    assert os.path.exists(clientCertPath)
    assert os.path.exists(serverCaPath)

    serverCertCommonName = 'localhost' # match hostname uses servers's cert commonname

    tymist = tyming.Tymist()
    with tcp.openServer(cls=tcp.ServerTls,
                    tymth=tymist.tymen(),
                    ha=("", 6101),
                    bs=16192,
                    keypath=serverKeyPath,
                    certpath=serverCertPath,
                    cafilepath=clientCaPath,
                    certify=ssl.CERT_REQUIRED,) as server, \
         tcp.openClient(cls=tcp.ClientTls,
                    tymth=tymist.tymen(),
                    ha=("127.0.0.1", 6101), bs=16192,
                    certedhost=serverCertCommonName,
                    keypath=clientKeyPath,
                    certpath=clientCertPath,
                    cafilepath=serverCaPath,
                    certify=ssl.CERT_NONE,
                    hostify=False,) as beta:

        assert server.opened == True
        assert server.eha == ('127.0.0.1', 6101)
        assert server.ha == ('0.0.0.0', 6101)

        assert beta.opened == True
        assert beta.accepted == False
        assert beta.connected == False
        assert beta.cutoff == False


        # Connect beta to server
        while not(beta.connected and len(server.ixes) >= 1):
            beta.serviceConnect()
            server.serviceConnects()
            time.sleep(0.01)

        assert beta.accepted == True
        assert beta.connected == True
        assert beta.cutoff == False
        assert beta.ca == beta.cs.getsockname()
        assert beta.ha == beta.cs.getpeername()

        ixBeta = server.ixes[beta.ca]
        assert ixBeta.cs.getsockname() == beta.cs.getpeername()
        assert ixBeta.cs.getpeername() == beta.cs.getsockname()
        assert ixBeta.ca == beta.ca
        assert ixBeta.ha == beta.ha

        msgOut = b"Beta sends to Server\n"
        beta.tx(msgOut)
        while not( not beta.txbs and ixBeta.rxbs):
            beta.serviceSends()
            server.serviceReceivesAllIx()
            time.sleep(0.01)

        time.sleep(0.05)
        server.serviceReceivesAllIx()

        msgIn = bytes(ixBeta.rxbs)
        assert msgIn == msgOut
        ixBeta.clearRxbs()

        msgOut = b'Server sends to Beta\n'
        ixBeta.tx(msgOut)
        while not (not ixBeta.txbs and beta.rxbs):
            server.serviceSendsAllIx()
            beta.serviceReceives()
            time.sleep(0.01)

        msgIn = bytes(beta.rxbs)
        assert msgIn == msgOut
        beta.clearRxbs()

    assert beta.opened == False
    assert server.opened == False
    """Done Test"""


def test_tcp_tls_verify_server():
    """
    Test TCP TLS client server connection with verify certs for server not client
    """

    certDirPath = localTestCertDirPath()
    assert os.path.exists(certDirPath)

    serverKeyPath = os.path.join(certDirPath, 'server_key.pem')  # local server private key
    serverCertPath = os.path.join(certDirPath, 'server_cert.pem')  # local server public cert
    clientCaPath = os.path.join(certDirPath, 'client.pem') # remote client public cert

    clientKeyPath = os.path.join(certDirPath, 'client_key.pem')  # local client private key
    clientCertPath = os.path.join(certDirPath, 'client_cert.pem')  # local client public cert
    serverCaPath = os.path.join(certDirPath, 'server.pem') # remote server public cert

    assert os.path.exists(serverKeyPath)
    assert os.path.exists(serverCertPath)
    assert os.path.exists(clientCaPath)
    assert os.path.exists(clientKeyPath)
    assert os.path.exists(clientCertPath)
    assert os.path.exists(serverCaPath)

    serverCertCommonName = 'localhost' # match hostname uses servers's cert commonname

    tymist = tyming.Tymist()
    with tcp.openServer(cls=tcp.ServerTls,
                    tymth=tymist.tymen(),
                    ha=("", 6101),
                    bs=16192,
                    keypath=serverKeyPath,
                    certpath=serverCertPath,
                    cafilepath=clientCaPath,
                    certify=ssl.CERT_NONE ,) as server, \
         tcp.openClient(cls=tcp.ClientTls,
                    tymth=tymist.tymen(),
                    ha=("127.0.0.1", 6101),
                    bs=16192,
                    certedhost=serverCertCommonName,
                    keypath=clientKeyPath,
                    certpath=clientCertPath,
                    cafilepath=serverCaPath,
                    certify=ssl.CERT_REQUIRED,
                    hostify=True,) as beta:

        assert server.opened == True
        assert server.eha == ('127.0.0.1', 6101)
        assert server.ha == ('0.0.0.0', 6101)

        assert beta.opened == True
        assert beta.accepted == False
        assert beta.connected == False
        assert beta.cutoff == False


        # Connect beta to server
        while not(beta.connected and len(server.ixes) >= 1):
            beta.serviceConnect()
            server.serviceConnects()
            time.sleep(0.01)

        assert beta.accepted == True
        assert beta.connected == True
        assert beta.cutoff == False
        assert beta.ca == beta.cs.getsockname()
        assert beta.ha == beta.cs.getpeername()

        ixBeta = server.ixes[beta.ca]
        assert ixBeta.cs.getsockname() == beta.cs.getpeername()
        assert ixBeta.cs.getpeername() == beta.cs.getsockname()
        assert ixBeta.ca == beta.ca
        assert ixBeta.ha == beta.ha

        msgOut = b"Beta sends to Server\n"
        beta.tx(msgOut)
        while not( not beta.txbs and ixBeta.rxbs):
            beta.serviceSends()
            server.serviceReceivesAllIx()
            time.sleep(0.01)

        time.sleep(0.05)
        server.serviceReceivesAllIx()

        msgIn = bytes(ixBeta.rxbs)
        assert msgIn == msgOut
        ixBeta.clearRxbs()

        msgOut = b'Server sends to Beta\n'
        ixBeta.tx(msgOut)
        while not (not ixBeta.txbs and beta.rxbs):
            server.serviceSendsAllIx()
            beta.serviceReceives()
            time.sleep(0.01)

        msgIn = bytes(beta.rxbs)
        assert msgIn == msgOut
        beta.clearRxbs()

    assert beta.opened == False
    assert server.opened == False
    """Done Test"""


def test_tcp_tls_verify_neither():
    """
    Test TCP TLS client server connection with verify certs for neither server nor client
    """

    certDirPath = localTestCertDirPath()
    assert os.path.exists(certDirPath)

    serverKeyPath = os.path.join(certDirPath, 'server_key.pem')  # local server private key
    serverCertPath = os.path.join(certDirPath, 'server_cert.pem')  # local server public cert
    clientCaPath = os.path.join(certDirPath, 'client.pem') # remote client public cert

    clientKeyPath = os.path.join(certDirPath, 'client_key.pem')  # local client private key
    clientCertPath = os.path.join(certDirPath, 'client_cert.pem')  # local client public cert
    serverCaPath = os.path.join(certDirPath, 'server.pem') # remote server public cert

    assert os.path.exists(serverKeyPath)
    assert os.path.exists(serverCertPath)
    assert os.path.exists(clientCaPath)
    assert os.path.exists(clientKeyPath)
    assert os.path.exists(clientCertPath)
    assert os.path.exists(serverCaPath)

    serverCertCommonName = 'localhost' # match hostname uses servers's cert commonname

    tymist = tyming.Tymist()
    with tcp.openServer(cls=tcp.ServerTls,
                    tymth=tymist.tymen(),
                    ha=("", 6101),
                    bs=16192,
                    keypath=serverKeyPath,
                    certpath=serverCertPath,
                    cafilepath=clientCaPath,
                    certify=ssl.CERT_NONE ,) as server, \
         tcp.openClient(cls=tcp.ClientTls,
                    tymth=tymist.tymen(),
                    ha=("127.0.0.1", 6101),
                    bs=16192,
                    certedhost=serverCertCommonName,
                    keypath=clientKeyPath,
                    certpath=clientCertPath,
                    cafilepath=serverCaPath,
                    certify=ssl.CERT_NONE,
                    hostify=False,) as beta:

        assert server.opened == True
        assert server.eha == ('127.0.0.1', 6101)
        assert server.ha == ('0.0.0.0', 6101)

        assert beta.opened == True
        assert beta.accepted == False
        assert beta.connected == False
        assert beta.cutoff == False


        # Connect beta to server
        while not(beta.connected and len(server.ixes) >= 1):
            beta.serviceConnect()
            server.serviceConnects()
            time.sleep(0.01)

        assert beta.accepted == True
        assert beta.connected == True
        assert beta.cutoff == False
        assert beta.ca == beta.cs.getsockname()
        assert beta.ha == beta.cs.getpeername()

        ixBeta = server.ixes[beta.ca]
        assert ixBeta.cs.getsockname() == beta.cs.getpeername()
        assert ixBeta.cs.getpeername() == beta.cs.getsockname()
        assert ixBeta.ca == beta.ca
        assert ixBeta.ha == beta.ha

        msgOut = b"Beta sends to Server\n"
        beta.tx(msgOut)
        while not( not beta.txbs and ixBeta.rxbs):
            beta.serviceSends()
            server.serviceReceivesAllIx()
            time.sleep(0.01)

        time.sleep(0.05)
        server.serviceReceivesAllIx()

        msgIn = bytes(ixBeta.rxbs)
        assert msgIn == msgOut
        ixBeta.clearRxbs()

        msgOut = b'Server sends to Beta\n'
        ixBeta.tx(msgOut)
        while not (not ixBeta.txbs and beta.rxbs):
            server.serviceSendsAllIx()
            beta.serviceReceives()
            time.sleep(0.01)

        msgIn = bytes(beta.rxbs)
        assert msgIn == msgOut
        beta.clearRxbs()

    assert beta.opened == False
    assert server.opened == False
    """Done Test"""


def test_tcp_tls_verify_both_tlsv12():
    """
    Test TCP TLS client server connection with verify certs for both client and server
    """

    certDirPath = localTestCertDirPath()
    assert os.path.exists(certDirPath)

    serverKeyPath = os.path.join(certDirPath, 'server_key.pem')  # local server private key
    serverCertPath = os.path.join(certDirPath, 'server_cert.pem')  # local server public cert
    clientCaPath = os.path.join(certDirPath, 'client.pem') # remote client public cert

    clientKeyPath = os.path.join(certDirPath, 'client_key.pem')  # local client private key
    clientCertPath = os.path.join(certDirPath, 'client_cert.pem')  # local client public cert
    serverCaPath = os.path.join(certDirPath, 'server.pem') # remote server public cert

    assert os.path.exists(serverKeyPath)
    assert os.path.exists(serverCertPath)
    assert os.path.exists(clientCaPath)
    assert os.path.exists(clientKeyPath)
    assert os.path.exists(clientCertPath)
    assert os.path.exists(serverCaPath)

    serverCertCommonName = 'localhost' # match hostname uses servers's cert commonname

    tymist = tyming.Tymist()
    with tcp.openServer(cls=tcp.ServerTls,
                    tymth=tymist.tymen(),
                    ha=("", 6101),
                    bs=16192,
                    keypath=serverKeyPath,
                    certpath=serverCertPath,
                    cafilepath=clientCaPath,
                    certify=ssl.CERT_REQUIRED,
                    version=ssl.PROTOCOL_TLSv1_2,) as server, \
         tcp.openClient(cls=tcp.ClientTls,
                    tymth=tymist.tymen(),
                    ha=("127.0.0.1", 6101),
                    bs=16192,
                    certedhost=serverCertCommonName,
                    keypath=clientKeyPath,
                    certpath=clientCertPath,
                    cafilepath=serverCaPath,
                    certify=ssl.CERT_REQUIRED,
                    hostify=True,
                    version=ssl.PROTOCOL_TLSv1_2,) as beta:


        assert server.opened == True
        assert server.eha == ('127.0.0.1', 6101)
        assert server.ha == ('0.0.0.0', 6101)

        assert beta.opened == True
        assert beta.accepted == False
        assert beta.connected == False
        assert beta.cutoff == False


        # Connect beta to server
        while not(beta.connected and len(server.ixes) >= 1):
            beta.serviceConnect()
            server.serviceConnects()
            time.sleep(0.01)

        assert beta.accepted == True
        assert beta.connected == True
        assert beta.cutoff == False
        assert beta.ca == beta.cs.getsockname()
        assert beta.ha == beta.cs.getpeername()

        ixBeta = server.ixes[beta.ca]
        assert ixBeta.cs.getsockname() == beta.cs.getpeername()
        assert ixBeta.cs.getpeername() == beta.cs.getsockname()
        assert ixBeta.ca == beta.ca
        assert ixBeta.ha == beta.ha

        msgOut = b"Beta sends to Server\n"
        beta.tx(msgOut)
        while not( not beta.txbs and ixBeta.rxbs):
            beta.serviceSends()
            server.serviceReceivesAllIx()
            time.sleep(0.01)

        time.sleep(0.05)
        server.serviceReceivesAllIx()

        msgIn = bytes(ixBeta.rxbs)
        assert msgIn == msgOut
        ixBeta.clearRxbs()

        msgOut = b'Server sends to Beta\n'
        ixBeta.tx(msgOut)
        while not (not ixBeta.txbs and beta.rxbs):
            server.serviceSendsAllIx()
            beta.serviceReceives()
            time.sleep(0.01)

        msgIn = bytes(beta.rxbs)
        assert msgIn == msgOut
        beta.clearRxbs()

    assert beta.opened == False
    assert server.opened == False
    """Done Test"""

def test_tcp_tls_server_with_client_abort_handshake():
    """
    Test TCP TLS client server connection with verify certs for server not client
    but test that server stays up in spite of client
    """

    certDirPath = localTestCertDirPath()
    assert os.path.exists(certDirPath)

    serverKeyPath = os.path.join(certDirPath, 'server_key.pem')  # local server private key
    serverCertPath = os.path.join(certDirPath, 'server_cert.pem')  # local server public cert
    clientCaPath = os.path.join(certDirPath, 'client.pem') # remote client public cert

    clientKeyPath = os.path.join(certDirPath, 'client_key.pem')  # local client private key
    clientCertPath = os.path.join(certDirPath, 'client_cert.pem')  # local client public cert
    serverCaPath = os.path.join(certDirPath, 'server.pem') # remote server public cert

    assert os.path.exists(serverKeyPath)
    assert os.path.exists(serverCertPath)
    assert os.path.exists(clientCaPath)
    assert os.path.exists(clientKeyPath)
    assert os.path.exists(clientCertPath)
    assert os.path.exists(serverCaPath)

    serverCertCommonName = 'localhost' # match hostname uses servers's cert commonname

    tymist = tyming.Tymist()
    with ( tcp.openServer(cls=tcp.ServerTls,
                    tymth=tymist.tymen(),
                    ha=("", 6101),
                    bs=16192,
                    keypath=serverKeyPath,
                    certpath=serverCertPath,
                    cafilepath=clientCaPath,
                    certify=ssl.CERT_NONE ,) as server,
          tcp.openClient(cls=tcp.ClientTls,
                    tymth=tymist.tymen(),
                    ha=("127.0.0.1", 6101),
                    bs=16192,
                    certedhost=serverCertCommonName,
                    keypath=clientKeyPath,
                    certpath=clientCertPath,
                    cafilepath=serverCaPath,
                    certify=ssl.CERT_REQUIRED,
                    hostify=True,) as beta
         ):

        assert server.opened == True
        assert server.eha == ('127.0.0.1', 6101)
        assert server.ha == ('0.0.0.0', 6101)

        assert beta.opened == True
        assert beta.accepted == False
        assert beta.connected == False
        assert beta.cutoff == False


        # Begine connection of client beta to server

        while not beta.connected and not server.cxes:
            beta.serviceConnect()
            server.serviceConnects()
            time.sleep(0.01)

        ca, cx = list(server.cxes.items())[0]  # handshake started
        assert not cx.connected  # handshake not completed success
        assert not cx.aborted  # handshake not completed fail

        beta.close()  # prematurely close client side of handshake
        time.sleep(0.01)
        assert not beta.opened
        server.serviceConnects()
        time.sleep(0.01)

        assert not server.cxes  # handshake aborted
        assert not server.ixes  # no incoming connection

        assert not beta.accepted
        assert not beta.connected
        assert not beta.cutoff
        assert not beta.cs

        # now beta tries again
        # Connect beta to server
        while not(beta.connected and server.ixes):
            beta.serviceConnect()
            server.serviceConnects()
            time.sleep(0.01)

        assert beta.accepted == True
        assert beta.connected == True
        assert beta.cutoff == False

        assert beta.ca == beta.cs.getsockname()
        assert beta.ha == beta.cs.getpeername()

        ixBeta = server.ixes[beta.ca]
        assert ixBeta.cs.getsockname() == beta.cs.getpeername()
        assert ixBeta.cs.getpeername() == beta.cs.getsockname()
        assert ixBeta.ca == beta.ca
        assert ixBeta.ha == beta.ha

        msgOut = b"Beta sends to Server\n"
        beta.tx(msgOut)
        while not( not beta.txbs and ixBeta.rxbs):
            beta.serviceSends()
            server.serviceReceivesAllIx()
            time.sleep(0.01)

        time.sleep(0.05)
        server.serviceReceivesAllIx()

        msgIn = bytes(ixBeta.rxbs)
        assert msgIn == msgOut
        ixBeta.clearRxbs()

        msgOut = b'Server sends to Beta\n'
        ixBeta.tx(msgOut)
        while not (not ixBeta.txbs and beta.rxbs):
            server.serviceSendsAllIx()
            beta.serviceReceives()
            time.sleep(0.01)

        msgIn = bytes(beta.rxbs)
        assert msgIn == msgOut
        beta.clearRxbs()

    assert beta.opened == False
    assert server.opened == False
    """Done Test"""


def test_server_client_doers():
    """
    Test ServerDoer ClientDoer classes
    """
    tock = 0.03125
    ticks = 16
    limit = ticks *  tock
    doist = doing.Doist(tock=tock, real=True, limit=limit)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == tock == 0.03125
    assert doist.real == True
    assert doist.limit == limit == 0.5
    assert doist.doers == []

    port = 6120
    server = tcp.Server(host="", port=port)
    # client needs tymth in order to init its .tymer
    client = tcp.Client(tymth=doist.tymen(), host="localhost", port=port)
    assert client.tyme == doist.tyme

    serdoer = tcp.ServerDoer(tymth=doist.tymen(), server=server)
    assert serdoer.server ==  server
    assert serdoer.tyme ==  serdoer.server.tyme == doist.tyme
    clidoer = tcp.ClientDoer(tymth=doist.tymen(), client=client)
    assert clidoer.client == client
    assert clidoer.tyme == clidoer.client.tyme == doist.tyme

    assert serdoer.tock == 0.0  # ASAP
    assert clidoer.tock == 0.0  # ASAP

    doers = [serdoer, clidoer]

    msgTx = b"Hello me maties!"
    clidoer.client.tx(msgTx)

    doist.do(doers=doers)
    assert doist.tyme == limit
    assert server.opened == False
    assert client.opened == False

    assert not client.txbs
    ca, ix = list(server.ixes.items())[0]
    msgRx = bytes(ix.rxbs)
    assert msgRx == msgTx

    """End Test """


def test_echo_server_client_doers():
    """
    Test EchoServerDoer ClientDoer classes
    """
    tock = 0.03125
    ticks = 16
    limit = ticks *  tock
    doist = doing.Doist(tock=tock, real=True, limit=limit)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == tock == 0.03125
    assert doist.real == True
    assert doist.limit == limit == 0.5
    assert doist.doers == []

    port = 6120
    server = tcp.Server(host="", port=port)
    client = tcp.Client(tymth=doist.tymen(), host="localhost", port=port)

    serdoer = tcp.EchoServerDoer(tymth=doist.tymen(), server=server)
    assert serdoer.server == server
    assert serdoer.tyme ==  serdoer.server.tyme == doist.tyme
    clidoer = tcp.ClientDoer(tymth=doist.tymen(), client=client)
    assert clidoer.client == client
    assert clidoer.tyme == clidoer.client.tyme == doist.tyme

    assert serdoer.tock == 0.0  # ASAP
    assert clidoer.tock == 0.0  # ASAP

    doers = [serdoer, clidoer]

    msgTx = b"Hello me maties!"
    clidoer.client.tx(msgTx)

    doist.do(doers=doers)
    assert doist.tyme == limit
    assert server.opened == False
    assert client.opened == False

    assert not client.txbs
    msgEx = bytes(client.rxbs)  # echoed back message
    assert msgEx == msgTx

    ca, ix = list(server.ixes.items())[0]
    assert bytes(ix.rxbs) == b""  # empty server rxbs becaue echoed
    """End Test """


if __name__ == "__main__":
    test_tcp_tls_server_with_client_abort_handshake()
