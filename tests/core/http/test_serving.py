# -*- coding: utf-8 -*-
"""
Unittests for http serving module
"""
import sys
import os
import time

import pytest

from hio import help
from hio.base import tyming
from hio.core import wiring
from hio.core.http import httping, clienting, serving

logger = help.ogler.getLogger()




def testHttpError(self):
    """
    Test HTTPError class
    """
    console.terse("{0}\n".format(self.testHttpError.__doc__))

    error = httping.HTTPError(status=400)
    self.assertEqual(error.status, 400)
    self.assertEqual(error.reason, 'Bad Request')
    self.assertEqual(error.title, "")
    self.assertEqual(error.detail, "")
    self.assertIs(error.fault, None)
    self.assertEqual(error.headers, dict())

    body = error.render()
    self.assertEqual(body, b'400 Bad Request\n\n\n')
    body = error.render(jsonify=True)
    self.assertEqual(body, (b'{\n  "status": 400,\n  "reason": "Bad Request",\n'
                            b'  "title": "",\n  "detail":'
                            b' "",\n  "fault": null\n}')
                           )

    error = httping.HTTPError(status=700,
                              title="Validation Error",
                              detail="Bad mojo",
                              fault=50,
                              headers=dict(Accept='application/json'))

    self.assertEqual(error.status, 700)
    self.assertEqual(error.reason, 'Unknown')
    self.assertEqual(error.title, "Validation Error")
    self.assertEqual(error.detail, "Bad mojo")
    self.assertIs(error.fault, 50)
    self.assertEqual(error.headers, dict(Accept='application/json'))

    body = error.render()
    self.assertEqual(body, b'700 Unknown\nValidation Error\nBad mojo\n50')
    body = error.render(jsonify=True)
    self.assertEqual(body, (b'{\n  "status": 700,\n  "reason": "Unknown",\n'
                            b'  "title": "Validation Error",'
                            b'\n  "detail": "Bad mojo",\n  "fault": 50\n}'))

def testPorterServiceEcho(self):
    """
    Test Porter service request response of echo non blocking
    """
    console.terse("{0}\n".format(self.testPorterServiceEcho.__doc__))


    tymist = tyming.Tymist(tyme=0.0)

    console.terse("{0}\n".format("Building Valet ...\n"))
    wireLogAlpha = wiring.WireLog(buffify=True, same=True)
    result = wireLogAlpha.reopen()

    alpha = serving.Porter(port = 6101,
                          bufsize=131072,
                          wlog=wireLogAlpha,
                          tymth=tymist.tymen())
    self.assertIs(alpha.servant.reopen(), True)
    self.assertEqual(alpha.servant.ha, ('0.0.0.0', 6101))
    self.assertEqual(alpha.servant.eha, ('127.0.0.1', 6101))

    console.terse("{0}\n".format("Building Patron ...\n"))
    wireLogBeta = wiring.WireLog(buffify=True,  same=True)
    result = wireLogBeta.reopen()

    path = "http://{0}:{1}/".format('localhost', alpha.servant.eha[1])

    beta = clienting.Patron(bufsize=131072,
                                 wlog=wireLogBeta,
                                 tymth=tymist.tymen(),
                                 path=path,
                                 reconnectable=True,
                                 )

    self.assertIs(beta.connector.reopen(), True)
    self.assertIs(beta.connector.accepted, False)
    self.assertIs(beta.connector.connected, False)
    self.assertIs(beta.connector.cutoff, False)

    request = dict([('method', u'GET'),
                     ('path', u'/echo?name=fame'),
                     ('qargs', dict()),
                     ('fragment', u''),
                     ('headers', dict([('Accept', 'application/json'),
                                        ('Content-Length', 0)])),
                    ])

    beta.requests.append(request)

    while (beta.requests or beta.connector.txes or not beta.responses or
           not alpha.servant.ixes or not alpha.idle()):
        alpha.serviceAll()
        time.sleep(0.05)
        beta.serviceAll()
        time.sleep(0.05)

    self.assertIs(beta.connector.accepted, True)
    self.assertIs(beta.connector.connected, True)
    self.assertIs(beta.connector.cutoff, False)

    self.assertEqual(len(alpha.servant.ixes), 1)
    self.assertEqual(len(alpha.stewards), 1)
    requestant = alpha.stewards.values()[0].requestant
    self.assertEqual(requestant.method, request['method'])
    self.assertEqual(requestant.url, request['path'])
    self.assertEqual(requestant.headers, {'accept': 'application/json',
                                            'accept-encoding': 'identity',
                                            'content-length': '0',
                                            'host': 'localhost:6101'})


    self.assertEqual(len(beta.responses), 1)
    response = beta.responses.popleft()
    self.assertEqual(response['data'],{'body': '',
                                    'data': None,
                                    'fragment': '',
                                    'headers': {'accept': 'application/json',
                                                'accept-encoding': 'identity',
                                                'content-length': '0',
                                                'host': 'localhost:6101'},
                                    'method': 'GET',
                                    'path': '/echo',
                                    'qargs': {'name': 'fame'},
                                    'version': 'HTTP/1.1'})

    responder = alpha.stewards.values()[0].responder
    self.assertEqual(responder.status, response['status'])
    self.assertEqual(responder.headers, response['headers'])

    alpha.servant.closeAll()
    beta.connector.close()

    wireLogAlpha.close()
    wireLogBeta.close()


def testValetServiceBasic(self):
    """
    Test Valet WSGI service request response
    """
    console.terse("{0}\n".format(self.testValetServiceBasic.__doc__))

    tymist = tyming.Tymist(tyme=0.0)

    def wsgiApp(environ, start_response):
        start_response('200 OK', [('Content-type','text/plain'),
                                  ('Content-length', '12')])
        return [b"Hello World!"]

    console.terse("{0}\n".format("Building Valet ...\n"))
    wireLogAlpha = wiring.WireLog(buffify=True, same=True)
    result = wireLogAlpha.reopen()

    alpha = serving.Valet(port = 6101,
                          bufsize=131072,
                          wlog=wireLogAlpha,
                          tymth=tymist.tymen(),
                          app=wsgiApp)
    self.assertIs(alpha.servant.reopen(), True)
    self.assertEqual(alpha.servant.ha, ('0.0.0.0', 6101))
    self.assertEqual(alpha.servant.eha, ('127.0.0.1', 6101))

    console.terse("{0}\n".format("Building Patron ...\n"))
    wireLogBeta = wiring.WireLog(buffify=True,  same=True)
    result = wireLogBeta.reopen()

    path = "http://{0}:{1}/".format('localhost', alpha.servant.eha[1])

    beta = clienting.Patron(bufsize=131072,
                                 wlog=wireLogBeta,
                                 tymth=tymist.tymen(),
                                 path=path,
                                 reconnectable=True,
                                 )

    self.assertIs(beta.connector.reopen(), True)
    self.assertIs(beta.connector.accepted, False)
    self.assertIs(beta.connector.connected, False)
    self.assertIs(beta.connector.cutoff, False)

    request = dict([('method', u'GET'),
                     ('path', u'/echo?name=fame'),
                     ('qargs', dict()),
                     ('fragment', u''),
                     ('headers', dict([('Accept', 'application/json'),
                                        ('Content-Length', 0)])),
                    ])

    beta.requests.append(request)

    while (beta.requests or beta.connector.txes or not beta.responses or
           not alpha.idle()):
        alpha.serviceAll()
        time.sleep(0.05)
        beta.serviceAll()
        time.sleep(0.05)

    self.assertIs(beta.connector.accepted, True)
    self.assertIs(beta.connector.connected, True)
    self.assertIs(beta.connector.cutoff, False)

    self.assertEqual(len(alpha.servant.ixes), 1)
    self.assertEqual(len(alpha.reqs), 1)
    self.assertEqual(len(alpha.reps), 1)
    requestant = alpha.reqs.values()[0]
    self.assertEqual(requestant.method, request['method'])
    self.assertEqual(requestant.url, request['path'])
    self.assertEqual(requestant.headers, {'accept': 'application/json',
                                            'accept-encoding': 'identity',
                                            'content-length': '0',
                                            'host': 'localhost:6101'})


    self.assertEqual(len(beta.responses), 1)
    response = beta.responses.popleft()
    self.assertEqual(response['body'],bytearray(b'Hello World!'))
    self.assertEqual(response['status'], 200)

    responder = alpha.reps.values()[0]
    self.assertTrue(responder.status.startswith, str(response['status']))
    self.assertEqual(responder.headers, response['headers'])

    alpha.servant.closeAll()
    beta.connector.close()

    wireLogAlpha.close()
    wireLogBeta.close()

def testValetServiceBottle(self):
    """
    Test Valet WSGI service request response
    """
    console.terse("{0}\n".format(self.testValetServiceBottle.__doc__))

    try:
        import bottle
    except ImportError as ex:
        console.terse("Bottle not available.\n")
        return

    tymist = tyming.Tymist(tyme=0.0)

    app = bottle.default_app() # create bottle app

    @app.get('/echo')
    @app.get('/echo/<action>')
    @app.post('/echo')
    @app.post('/echo/<action>')
    def echoGet(action=None):
        """
        Echo back request data
        """
        query = dict(bottle.request.query.items())
        body = bottle.request.json
        raw = bottle.request.body.read()
        form = dict(bottle.request.forms)

        data = dict(verb=bottle.request.method,
                    url=bottle.request.url,
                    action=action,
                    query=query,
                    form=form,
                    content=body)
        return data


    console.terse("{0}\n".format("Building Valet ...\n"))
    wireLogAlpha = wiring.WireLog(buffify=True, same=True)
    result = wireLogAlpha.reopen()

    alpha = serving.Valet(port = 6101,
                          bufsize=131072,
                          wlog=wireLogAlpha,
                          tymth=tymist.tymen(),
                          app=app)
    self.assertIs(alpha.servant.reopen(), True)
    self.assertEqual(alpha.servant.ha, ('0.0.0.0', 6101))
    self.assertEqual(alpha.servant.eha, ('127.0.0.1', 6101))

    console.terse("{0}\n".format("Building Patron ...\n"))
    wireLogBeta = wiring.WireLog(buffify=True,  same=True)
    result = wireLogBeta.reopen()

    path = "http://{0}:{1}/".format('localhost', alpha.servant.eha[1])

    beta = clienting.Patron(bufsize=131072,
                                 wlog=wireLogBeta,
                                 tymth=tymist.tymen(),
                                 path=path,
                                 reconnectable=True,
                                 )

    self.assertIs(beta.connector.reopen(), True)
    self.assertIs(beta.connector.accepted, False)
    self.assertIs(beta.connector.connected, False)
    self.assertIs(beta.connector.cutoff, False)

    request = dict([('method', u'GET'),
                     ('path', u'/echo?name=fame'),
                     ('qargs', dict()),
                     ('fragment', u''),
                     ('headers', dict([('Accept', 'application/json'),
                                        ('Content-Length', 0)])),
                    ])

    beta.requests.append(request)
    tymer = tyming.Tymer(tymth=tymist.tymen(), duration=1.0)
    while (beta.requests or beta.connector.txes or not beta.responses or
           not alpha.idle()):
        alpha.serviceAll()
        time.sleep(0.05)
        beta.serviceAll()
        time.sleep(0.05)
        tymist.tick(tock=0.1)

    self.assertIs(beta.connector.accepted, True)
    self.assertIs(beta.connector.connected, True)
    self.assertIs(beta.connector.cutoff, False)

    self.assertEqual(len(alpha.servant.ixes), 1)
    self.assertEqual(len(alpha.reqs), 1)
    self.assertEqual(len(alpha.reps), 1)
    requestant = alpha.reqs.values()[0]
    self.assertEqual(requestant.method, request['method'])
    self.assertEqual(requestant.url, request['path'])
    self.assertEqual(requestant.headers, {'accept': 'application/json',
                                            'accept-encoding': 'identity',
                                            'content-length': '0',
                                            'host': 'localhost:6101'})

    self.assertEqual(len(beta.responses), 1)
    response = beta.responses.popleft()
    self.assertEqual(response['status'], 200)
    self.assertEqual(response['reason'], 'OK')
    self.assertEqual(response['body'], bytearray(b'{"verb": "GET", "url": "http://localhost:6101/echo?name=fame", "'
                                                    b'action": null, "query": {"name": "fame"}, "form": {}, "content":'
                                                    b' null}')
                                          )
    self.assertEqual(response['data'],{'action': None,
                                        'content': None,
                                        'form': {},
                                        'query': {'name': 'fame'},
                                        'url': 'http://localhost:6101/echo?name=fame',
                                        'verb': 'GET'},)

    responder = alpha.reps.values()[0]
    self.assertTrue(responder.status.startswith, str(response['status']))
    self.assertEqual(responder.headers, response['headers'])

    alpha.servant.closeAll()
    beta.connector.close()

    wireLogAlpha.close()
    wireLogBeta.close()

def testValetServiceBottleNoContentLength(self):
    """
    Test Valet WSGI service request response no content-length in request
    """
    console.terse("{0}\n".format(self.testValetServiceBottleNoContentLength.__doc__))

    try:
        import bottle
    except ImportError as ex:
        console.terse("Bottle not available.\n")
        return

    tymist = tyming.Tymist(tyme=0.0)

    app = bottle.default_app() # create bottle app

    @app.get('/echo')
    @app.get('/echo/<action>')
    @app.post('/echo')
    @app.post('/echo/<action>')
    def echoGet(action=None):
        """
        Echo back request data
        """
        query = dict(bottle.request.query.items())
        body = bottle.request.json
        raw = bottle.request.body.read()
        form = dict(bottle.request.forms)

        data = dict(verb=bottle.request.method,
                    url=bottle.request.url,
                    action=action,
                    query=query,
                    form=form,
                    content=body)
        return data


    console.terse("{0}\n".format("Building Valet ...\n"))
    wireLogAlpha = wiring.WireLog(buffify=True, same=True)
    result = wireLogAlpha.reopen()

    alpha = serving.Valet(port = 6101,
                          bufsize=131072,
                          wlog=wireLogAlpha,
                          tymth=tymist.tymen(),
                          app=app)
    self.assertIs(alpha.servant.reopen(), True)
    self.assertEqual(alpha.servant.ha, ('0.0.0.0', 6101))
    self.assertEqual(alpha.servant.eha, ('127.0.0.1', 6101))

    console.terse("{0}\n".format("Building Patron ...\n"))
    wireLogBeta = wiring.WireLog(buffify=True,  same=True)
    result = wireLogBeta.reopen()

    path = "http://{0}:{1}/".format('localhost', alpha.servant.eha[1])

    beta = clienting.Patron(bufsize=131072,
                                 wlog=wireLogBeta,
                                 tymth=tymist.tymen(),
                                 path=path,
                                 reconnectable=True,
                                 )

    self.assertIs(beta.connector.reopen(), True)
    self.assertIs(beta.connector.accepted, False)
    self.assertIs(beta.connector.connected, False)
    self.assertIs(beta.connector.cutoff, False)

    request = dict([('method', u'GET'),
                     ('path', u'/echo?name=fame'),
                     ('qargs', dict()),
                     ('fragment', u''),
                     ('headers', dict([('Accept', 'application/json'),
                                        ])),
                    ])

    beta.requests.append(request)
    tymer = tyming.Tymer(tymth=tymist.tymen(), duration=1.0)
    while (beta.requests or beta.connector.txes or not beta.responses or
           not alpha.idle()):
        alpha.serviceAll()
        time.sleep(0.05)
        beta.serviceAll()
        time.sleep(0.05)
        tymist.tick(tock=0.1)

    self.assertIs(beta.connector.accepted, True)
    self.assertIs(beta.connector.connected, True)
    self.assertIs(beta.connector.cutoff, False)

    self.assertEqual(len(alpha.servant.ixes), 1)
    self.assertEqual(len(alpha.reqs), 1)
    self.assertEqual(len(alpha.reps), 1)
    requestant = alpha.reqs.values()[0]
    self.assertEqual(requestant.method, request['method'])
    self.assertEqual(requestant.url, request['path'])
    self.assertEqual(requestant.headers, {'accept': 'application/json',
                                            'accept-encoding': 'identity',
                                            'host': 'localhost:6101'})

    self.assertEqual(len(beta.responses), 1)
    response = beta.responses.popleft()
    self.assertEqual(response['status'], 200)
    self.assertEqual(response['reason'], 'OK')
    self.assertEqual(response['body'], bytearray(b'{"verb": "GET", "url": "http://localhost:6101/echo?name=fame", "'
                                                    b'action": null, "query": {"name": "fame"}, "form": {}, "content":'
                                                    b' null}'))
    self.assertEqual(response['data'],{'action': None,
                                        'content': None,
                                        'form': {},
                                        'query': {'name': 'fame'},
                                        'url': 'http://localhost:6101/echo?name=fame',
                                        'verb': 'GET'},)

    responder = alpha.reps.values()[0]
    self.assertTrue(responder.status.startswith, str(response['status']))
    self.assertEqual(responder.headers, response['headers'])

    alpha.servant.closeAll()
    beta.connector.close()

    wireLogAlpha.close()
    wireLogBeta.close()

def testValetServiceBottleNonPersistent(self):
    """
    Test Valet WSGI service request response non persistent connection in request
    """
    console.terse("{0}\n".format(self.testValetServiceBottleNonPersistent.__doc__))

    try:
        import bottle
    except ImportError as ex:
        console.terse("Bottle not available.\n")
        return

    tymist = tyming.Tymist(tyme=0.0)

    app = bottle.default_app() # create bottle app

    @app.get('/echo')
    @app.get('/echo/<action>')
    @app.post('/echo')
    @app.post('/echo/<action>')
    def echoGet(action=None):
        """
        Echo back request data
        """
        query = dict(bottle.request.query.items())
        body = bottle.request.json
        raw = bottle.request.body.read()
        form = dict(bottle.request.forms)

        data = dict(verb=bottle.request.method,
                    url=bottle.request.url,
                    action=action,
                    query=query,
                    form=form,
                    content=body)
        return data


    console.terse("{0}\n".format("Building Valet ...\n"))
    wireLogAlpha = wiring.WireLog(buffify=True, same=True)
    result = wireLogAlpha.reopen()

    alpha = serving.Valet(port = 6101,
                          bufsize=131072,
                          wlog=wireLogAlpha,
                          tymth=tymist.tymen(),
                          app=app)
    self.assertIs(alpha.servant.reopen(), True)
    self.assertEqual(alpha.servant.ha, ('0.0.0.0', 6101))
    self.assertEqual(alpha.servant.eha, ('127.0.0.1', 6101))

    console.terse("{0}\n".format("Building Patron ...\n"))
    wireLogBeta = wiring.WireLog(buffify=True,  same=True)
    result = wireLogBeta.reopen()

    path = "http://{0}:{1}/".format('localhost', alpha.servant.eha[1])

    beta = clienting.Patron(bufsize=131072,
                                 wlog=wireLogBeta,
                                 tymth=tymist.tymen(),
                                 path=path,
                                 reconnectable=True,
                                 )

    self.assertIs(beta.connector.reopen(), True)
    self.assertIs(beta.connector.accepted, False)
    self.assertIs(beta.connector.connected, False)
    self.assertIs(beta.connector.cutoff, False)

    request = dict([('method', u'GET'),
                     ('path', u'/echo?name=fame'),
                     ('qargs', dict()),
                     ('fragment', u''),
                     ('headers', dict([('Accept', 'application/json'),
                                        ('Connection', 'close')])),
                    ])

    beta.requests.append(request)
    tymer = tyming.Tymer(tymth=tymist.tymen(), duration=1.0)
    while (beta.requests or beta.connector.txes or not beta.responses or
           not alpha.idle()):
        alpha.serviceAll()
        time.sleep(0.05)
        beta.serviceAll()
        time.sleep(0.05)
        tymist.tick(tock=0.1)

    self.assertIs(beta.connector.accepted, True)
    self.assertIs(beta.connector.connected, True)
    self.assertIs(beta.connector.cutoff, False)

    self.assertEqual(len(alpha.servant.ixes), 1)
    self.assertEqual(len(alpha.reqs), 1)
    self.assertEqual(len(alpha.reps), 1)
    requestant = alpha.reqs.values()[0]
    self.assertEqual(requestant.method, request['method'])
    self.assertEqual(requestant.url, request['path'])
    self.assertEqual(requestant.headers, {'accept': 'application/json',
                                            'accept-encoding': 'identity',
                                            'host': 'localhost:6101',
                                            'connection': 'close',})

    self.assertEqual(len(beta.responses), 1)
    response = beta.responses.popleft()
    self.assertEqual(response['status'], 200)
    self.assertEqual(response['reason'], 'OK')
    self.assertEqual(response['body'], bytearray(b'{"verb": "GET", "url": "http://localhost:6101/echo?name=fame", "'
                                                    b'action": null, "query": {"name": "fame"}, "form": {}, "content":'
                                                    b' null}'))
    self.assertEqual(response['data'],{'action': None,
                                        'content': None,
                                        'form': {},
                                        'query': {'name': 'fame'},
                                        'url': 'http://localhost:6101/echo?name=fame',
                                        'verb': 'GET'},)

    responder = alpha.reps.values()[0]
    self.assertTrue(responder.status.startswith, str(response['status']))
    self.assertEqual(responder.headers, response['headers'])

    alpha.servant.closeAll()
    beta.connector.close()

    wireLogAlpha.close()
    wireLogBeta.close()

def testValetServiceBottleStream(self):
    """
    Test Valet WSGI service request response stream sse
    """
    console.terse("{0}\n".format(self.testValetServiceBottleStream.__doc__))

    try:
        import bottle
    except ImportError as ex:
        console.terse("Bottle not available.\n")
        return

    tymist = tyming.Tymist(tyme=0.0)

    app = bottle.default_app() # create bottle app

    @app.get('/stream')
    def streamGet():
        """
        Create test server sent event stream that sends count events
        """
        tymer = tyming.Tymer(tymth=tymist.tymen(), duration=2.0)
        bottle.response.set_header('Content-Type',  'text/event-stream') #text
        bottle.response.set_header('Cache-Control',  'no-cache')
        # HTTP 1.1 servers detect text/event-stream and use Transfer-Encoding: chunked
        # Set client-side auto-reconnect timeout, ms.
        yield 'retry: 1000\n\n'
        i = 0
        yield 'id: {0}\n'.format(i)
        i += 1
        yield 'data: START\n\n'
        n = 1
        while not tymer.expired:
            yield 'id: {0}\n'.format(i)
            i += 1
            yield 'data: {0}\n\n'.format(n)
            n += 1
        yield "data: END\n\n"

    console.terse("{0}\n".format("Building Valet ...\n"))
    wireLogAlpha = wiring.WireLog(buffify=True, same=True)
    result = wireLogAlpha.reopen()

    alpha = serving.Valet(port = 6101,
                          bufsize=131072,
                          wlog=wireLogAlpha,
                          tymth=tymist.tymen(),
                          app=app)
    self.assertIs(alpha.servant.reopen(), True)
    self.assertEqual(alpha.servant.ha, ('0.0.0.0', 6101))
    self.assertEqual(alpha.servant.eha, ('127.0.0.1', 6101))

    console.terse("{0}\n".format("Building Patron ...\n"))
    wireLogBeta = wiring.WireLog(buffify=True,  same=True)
    result = wireLogBeta.reopen()

    path = "http://{0}:{1}/".format('localhost', alpha.servant.eha[1])

    beta = clienting.Patron(bufsize=131072,
                                 wlog=wireLogBeta,
                                 tymth=tymist.tymen(),
                                 path=path,
                                 reconnectable=True,
                                 )

    self.assertIs(beta.connector.reopen(), True)
    self.assertIs(beta.connector.accepted, False)
    self.assertIs(beta.connector.connected, False)
    self.assertIs(beta.connector.cutoff, False)

    request = dict([('method', u'GET'),
                     ('path', u'/stream'),
                     ('qargs', dict()),
                     ('fragment', u''),
                     ('headers', dict([('Accept', 'application/json'),
                                        ('Content-Length', 0)])),
                     ('body', None),
                    ])

    beta.requests.append(request)
    tymer = tyming.Tymer(tymth=tymist.tymen(), duration=1.0)
    while (not tymer.expired):
        alpha.serviceAll()
        time.sleep(0.05)
        beta.serviceAll()
        time.sleep(0.05)
        tymist.tock(tock=0.1)

    self.assertIs(beta.connector.accepted, True)
    self.assertIs(beta.connector.connected, True)
    self.assertIs(beta.connector.cutoff, False)

    self.assertEqual(len(alpha.servant.ixes), 1)
    self.assertEqual(len(alpha.reqs), 1)
    self.assertEqual(len(alpha.reps), 1)
    requestant = alpha.reqs.values()[0]
    self.assertEqual(requestant.method, request['method'])
    self.assertEqual(requestant.url, request['path'])
    self.assertEqual(requestant.headers, {'accept': 'application/json',
                                            'accept-encoding': 'identity',
                                            'content-length': '0',
                                            'host': 'localhost:6101'})


    #timed out while stream still open so no responses in .responses
    self.assertIs(beta.waited, True)
    self.assertIs(beta.respondent.ended, False)
    self.assertEqual(len(beta.responses), 0)
    self.assertIn('content-type', beta.respondent.headers)
    self.assertEqual(beta.respondent.headers['content-type'], 'text/event-stream')
    self.assertIn('transfer-encoding', beta.respondent.headers)
    self.assertEqual(beta.respondent.headers['transfer-encoding'], 'chunked')

    self.assertTrue(len(beta.events) >= 3)
    self.assertEqual(beta.respondent.retry, 1000)
    self.assertTrue(int(beta.respondent.leid) >= 2)
    event = beta.events.popleft()
    self.assertEqual(event, {'id': '0', 'name': '', 'data': 'START'})
    event = beta.events.popleft()
    self.assertEqual(event, {'id': '1', 'name': '', 'data': '1'})
    event = beta.events.popleft()
    self.assertEqual(event, {'id': '2', 'name': '', 'data': '2'})
    beta.events.clear()

    #keep going until ended
    tymer.restart(duration=1.5)
    while (not tymer.expired):
        alpha.serviceAll()
        time.sleep(0.05)
        beta.serviceAll()
        time.sleep(0.05)
        tymist.tick(tock=0.1)

    self.assertTrue(len(beta.events) >= 3)
    self.assertEqual(beta.respondent.leid,  '9')
    self.assertEqual(beta.events[-2], {'id': '9', 'name': '', 'data': '9'})
    self.assertEqual(beta.events[-1], {'id': '9', 'name': '', 'data': 'END'})
    beta.events.clear()

    alpha.servant.closeAll()
    beta.connector.close()

    wireLogAlpha.close()
    wireLogBeta.close()

def testValetServiceBasicSecure(self):
    """
    Test Valet WSGI service with secure TLS request response
    """
    console.terse("{0}\n".format(self.testValetServiceBasicSecure.__doc__))

    tymist = tyming.Tymist(tyme=0.0)

    def wsgiApp(environ, start_response):
        start_response('200 OK', [('Content-type','text/plain'),
                                  ('Content-length', '12')])
        return [b"Hello World!"]

    console.terse("{0}\n".format("Building Valet ...\n"))
    wireLogAlpha = wiring.WireLog(buffify=True, same=True)
    result = wireLogAlpha.reopen()

    serverCertCommonName = 'localhost' # match hostname uses servers's cert commonname
    #serverKeypath = '/etc/pki/tls/certs/server_key.pem'  # local server private key
    #serverCertpath = '/etc/pki/tls/certs/server_cert.pem'  # local server public cert
    #clientCafilepath = '/etc/pki/tls/certs/client.pem' # remote client public cert

    serverKeypath = self.certdirpath + '/server_key.pem'  # local server private key
    serverCertpath = self.certdirpath + '/server_cert.pem'  # local server public cert
    clientCafilepath = self.certdirpath + '/client.pem' # remote client public cert

    alpha = serving.Valet(port = 6101,
                          bufsize=131072,
                          wlog=wireLogAlpha,
                          tymth=tymist.tymen(),
                          app=wsgiApp,
                          scheme='https',
                          keypath=serverKeypath,
                          certpath=serverCertpath,
                          cafilepath=clientCafilepath,)

    self.assertIs(alpha.servant.reopen(), True)
    self.assertEqual(alpha.servant.ha, ('0.0.0.0', 6101))
    self.assertEqual(alpha.servant.eha, ('127.0.0.1', 6101))

    console.terse("{0}\n".format("Building Patron ...\n"))
    wireLogBeta = wiring.WireLog(buffify=True,  same=True)
    result = wireLogBeta.reopen()

    #clientKeypath = '/etc/pki/tls/certs/client_key.pem'  # local client private key
    #clientCertpath = '/etc/pki/tls/certs/client_cert.pem'  # local client public cert
    #serverCafilepath = '/etc/pki/tls/certs/server.pem' # remote server public cert

    clientKeypath = self.certdirpath + '/client_key.pem'  # local client private key
    clientCertpath = self.certdirpath + '/client_cert.pem'  # local client public cert
    serverCafilepath = self.certdirpath + '/server.pem' # remote server public cert

    path = "https://{0}:{1}/".format('localhost', alpha.servant.eha[1])

    beta = clienting.Patron(bufsize=131072,
                                 wlog=wireLogBeta,
                                 tymth=tymist.tymen(),
                                 path=path,
                                 reconnectable=True,
                                 scheme='https',
                                 certedhost=serverCertCommonName,
                                 keypath=clientKeypath,
                                 certpath=clientCertpath,
                                 cafilepath=serverCafilepath
                                 )

    self.assertIs(beta.connector.reopen(), True)
    self.assertIs(beta.connector.accepted, False)
    self.assertIs(beta.connector.connected, False)
    self.assertIs(beta.connector.cutoff, False)

    request = dict([('method', u'GET'),
                     ('path', u'/echo?name=fame'),
                     ('qargs', dict()),
                     ('fragment', u''),
                     ('headers', dict([('Accept', 'application/json'),
                                        ('Content-Length', 0)])),
                    ])

    beta.requests.append(request)

    while (beta.requests or beta.connector.txes or not beta.responses or
           not alpha.idle()):
        alpha.serviceAll()
        time.sleep(0.05)
        beta.serviceAll()
        time.sleep(0.05)

    self.assertIs(beta.connector.accepted, True)
    self.assertIs(beta.connector.connected, True)
    self.assertIs(beta.connector.cutoff, False)

    self.assertEqual(len(alpha.servant.ixes), 1)
    self.assertEqual(len(alpha.reqs), 1)
    self.assertEqual(len(alpha.reps), 1)
    requestant = alpha.reqs.values()[0]
    self.assertEqual(requestant.method, request['method'])
    self.assertEqual(requestant.url, request['path'])
    self.assertEqual(requestant.headers, {'accept': 'application/json',
                                            'accept-encoding': 'identity',
                                            'content-length': '0',
                                            'host': 'localhost:6101'})


    self.assertEqual(len(beta.responses), 1)
    response = beta.responses.popleft()
    self.assertEqual(response['body'],bytearray(b'Hello World!'))
    self.assertEqual(response['status'], 200)

    responder = alpha.reps.values()[0]
    self.assertTrue(responder.status.startswith, str(response['status']))
    self.assertEqual(responder.headers, response['headers'])

    alpha.servant.closeAll()
    beta.connector.close()

    wireLogAlpha.close()
    wireLogBeta.close()

def testValetServiceBottleSecure(self):
    """
    Test Valet WSGI service secure TLS request response
    """
    console.terse("{0}\n".format(self.testValetServiceBottleSecure.__doc__))

    try:
        import bottle
    except ImportError as ex:
        console.terse("Bottle not available.\n")
        return

    tymist = tyming.Tymist(tyme=0.0)

    app = bottle.default_app() # create bottle app

    @app.get('/echo')
    @app.get('/echo/<action>')
    @app.post('/echo')
    @app.post('/echo/<action>')
    def echoGet(action=None):
        """
        Echo back request data
        """
        query = dict(bottle.request.query.items())
        body = bottle.request.json
        raw = bottle.request.body.read()
        form = dict(bottle.request.forms)

        data = dict(verb=bottle.request.method,
                    url=bottle.request.url,
                    action=action,
                    query=query,
                    form=form,
                    content=body)
        return data


    console.terse("{0}\n".format("Building Valet ...\n"))
    wireLogAlpha = wiring.WireLog(buffify=True, same=True)
    result = wireLogAlpha.reopen()

    serverCertCommonName = 'localhost' # match hostname uses servers's cert commonname
    #serverKeypath = '/etc/pki/tls/certs/server_key.pem'  # local server private key
    #serverCertpath = '/etc/pki/tls/certs/server_cert.pem'  # local server public cert
    #clientCafilepath = '/etc/pki/tls/certs/client.pem' # remote client public cert

    serverKeypath = self.certdirpath + '/server_key.pem'  # local server private key
    serverCertpath = self.certdirpath + '/server_cert.pem'  # local server public cert
    clientCafilepath = self.certdirpath + '/client.pem' # remote client public cert

    alpha = serving.Valet(port = 6101,
                          bufsize=131072,
                          wlog=wireLogAlpha,
                          tymth=tymist.tymen(),
                          app=app,
                          scheme='https',
                          keypath=serverKeypath,
                          certpath=serverCertpath,
                          cafilepath=clientCafilepath,
                          )
    self.assertIs(alpha.servant.reopen(), True)
    self.assertEqual(alpha.servant.ha, ('0.0.0.0', 6101))
    self.assertEqual(alpha.servant.eha, ('127.0.0.1', 6101))

    console.terse("{0}\n".format("Building Patron ...\n"))
    wireLogBeta = wiring.WireLog(buffify=True,  same=True)
    result = wireLogBeta.reopen()

    #clientKeypath = '/etc/pki/tls/certs/client_key.pem'  # local client private key
    #clientCertpath = '/etc/pki/tls/certs/client_cert.pem'  # local client public cert
    #serverCafilepath = '/etc/pki/tls/certs/server.pem' # remote server public cert

    clientKeypath = self.certdirpath + '/client_key.pem'  # local client private key
    clientCertpath = self.certdirpath + '/client_cert.pem'  # local client public cert
    serverCafilepath = self.certdirpath + '/server.pem' # remote server public cert

    path = "https://{0}:{1}/".format('localhost', alpha.servant.eha[1])

    beta = clienting.Patron(bufsize=131072,
                            wlog=wireLogBeta,
                            tymth=tymist.tymen(),
                            path=path,
                            reconnectable=True,
                            scheme='https',
                            certedhost=serverCertCommonName,
                            keypath=clientKeypath,
                            certpath=clientCertpath,
                            cafilepath=serverCafilepath
                            )

    self.assertIs(beta.connector.reopen(), True)
    self.assertIs(beta.connector.accepted, False)
    self.assertIs(beta.connector.connected, False)
    self.assertIs(beta.connector.cutoff, False)

    request = dict([('method', u'GET'),
                     ('path', u'/echo?name=fame'),
                     ('qargs', dict()),
                     ('fragment', u''),
                     ('headers', dict([('Accept', 'application/json'),
                                        ('Content-Length', 0)])),
                    ])

    beta.requests.append(request)
    tymer = tyming.Tymer(tymth=tymist.tymen(), duration=1.0)
    while (beta.requests or beta.connector.txes or not beta.responses or
           not alpha.idle()):
        alpha.serviceAll()
        time.sleep(0.05)
        beta.serviceAll()
        time.sleep(0.05)
        tymist.tick(tock=0.1)

    self.assertIs(beta.connector.accepted, True)
    self.assertIs(beta.connector.connected, True)
    self.assertIs(beta.connector.cutoff, False)

    self.assertEqual(len(alpha.servant.ixes), 1)
    self.assertEqual(len(alpha.reqs), 1)
    self.assertEqual(len(alpha.reps), 1)
    requestant = alpha.reqs.values()[0]
    self.assertEqual(requestant.method, request['method'])
    self.assertEqual(requestant.url, request['path'])
    self.assertEqual(requestant.headers, {'accept': 'application/json',
                                            'accept-encoding': 'identity',
                                            'content-length': '0',
                                            'host': 'localhost:6101'})

    self.assertEqual(len(beta.responses), 1)
    response = beta.responses.popleft()
    self.assertEqual(response['status'], 200)
    self.assertEqual(response['reason'], 'OK')
    self.assertEqual(response['body'], bytearray(b'{"verb": "GET", "url": "https://localhost:6101/echo?name=fame", '
                                                b'"action": null, "query": {"name": "fame"}, "form": {}, "content"'
                                                b': null}'))
    self.assertEqual(response['data'],{'action': None,
                                        'content': None,
                                        'form': {},
                                        'query': {'name': 'fame'},
                                        'url': 'https://localhost:6101/echo?name=fame',
                                        'verb': 'GET'},)

    responder = alpha.reps.values()[0]
    self.assertTrue(responder.status.startswith, str(response['status']))
    self.assertEqual(responder.headers, response['headers'])

    alpha.servant.closeAll()
    beta.connector.close()

    wireLogAlpha.close()
    wireLogBeta.close()

def testValetServiceBottleStreamSecure(self):
    """
    Test Valet WSGI service request response stream sse
    """
    console.terse("{0}\n".format(self.testValetServiceBottleStreamSecure.__doc__))

    try:
        import bottle
    except ImportError as ex:
        console.terse("Bottle not available.\n")
        return

    tymist = tyming.Tymist(tyme=0.0)

    app = bottle.default_app() # create bottle app

    @app.get('/stream')
    def streamGet():
        """
        Create test server sent event stream that sends count events
        """
        tymer = tyming.Tymer(tymth=tymist.tymen(), duration=2.0)
        bottle.response.set_header('Content-Type',  'text/event-stream') #text
        bottle.response.set_header('Cache-Control',  'no-cache')
        # HTTP 1.1 servers detect text/event-stream and use Transfer-Encoding: chunked
        # Set client-side auto-reconnect timeout, ms.
        yield 'retry: 1000\n\n'
        i = 0
        yield 'id: {0}\n'.format(i)
        i += 1
        yield 'data: START\n\n'
        n = 1
        while not tymer.expired:
            yield 'id: {0}\n'.format(i)
            i += 1
            yield 'data: {0}\n\n'.format(n)
            n += 1
        yield "data: END\n\n"

    console.terse("{0}\n".format("Building Valet ...\n"))
    wireLogAlpha = wiring.WireLog(buffify=True, same=True)
    result = wireLogAlpha.reopen()

    serverCertCommonName = 'localhost' # match hostname uses servers's cert commonname
    #serverKeypath = '/etc/pki/tls/certs/server_key.pem'  # local server private key
    #serverCertpath = '/etc/pki/tls/certs/server_cert.pem'  # local server public cert
    #clientCafilepath = '/etc/pki/tls/certs/client.pem' # remote client public cert

    serverKeypath = self.certdirpath + '/server_key.pem'  # local server private key
    serverCertpath = self.certdirpath + '/server_cert.pem'  # local server public cert
    clientCafilepath = self.certdirpath + '/client.pem' # remote client public cert

    alpha = serving.Valet(port = 6101,
                          bufsize=131072,
                          wlog=wireLogAlpha,
                          tymth=tymist.tymen(),
                          app=app,
                          scheme='https',
                          keypath=serverKeypath,
                          certpath=serverCertpath,
                          cafilepath=clientCafilepath,
                          )
    self.assertIs(alpha.servant.reopen(), True)
    self.assertEqual(alpha.servant.ha, ('0.0.0.0', 6101))
    self.assertEqual(alpha.servant.eha, ('127.0.0.1', 6101))

    console.terse("{0}\n".format("Building Patron ...\n"))
    wireLogBeta = wiring.WireLog(buffify=True,  same=True)
    result = wireLogBeta.reopen()

    #clientKeypath = '/etc/pki/tls/certs/client_key.pem'  # local client private key
    #clientCertpath = '/etc/pki/tls/certs/client_cert.pem'  # local client public cert
    #serverCafilepath = '/etc/pki/tls/certs/server.pem' # remote server public cert

    clientKeypath = self.certdirpath + '/client_key.pem'  # local client private key
    clientCertpath = self.certdirpath + '/client_cert.pem'  # local client public cert
    serverCafilepath = self.certdirpath + '/server.pem' # remote server public cert

    path = "https://{0}:{1}/".format('localhost', alpha.servant.eha[1])

    beta = clienting.Patron(bufsize=131072,
                                 wlog=wireLogBeta,
                                 tymth=tymist.tymen(),
                                 path=path,
                                 reconnectable=True,
                                 scheme='https',
                                 certedhost=serverCertCommonName,
                                 keypath=clientKeypath,
                                 certpath=clientCertpath,
                                 cafilepath=serverCafilepath
                                 )

    self.assertIs(beta.connector.reopen(), True)
    self.assertIs(beta.connector.accepted, False)
    self.assertIs(beta.connector.connected, False)
    self.assertIs(beta.connector.cutoff, False)

    request = dict([('method', u'GET'),
                     ('path', u'/stream'),
                     ('qargs', dict()),
                     ('fragment', u''),
                     ('headers', dict([('Accept', 'application/json'),
                                        ('Content-Length', 0)])),
                     ('body', None),
                    ])

    beta.requests.append(request)
    tymer = tyming.Tymer(tymth=tymist.tymen(), duration=1.0)
    while (not timer.expired):
        alpha.serviceAll()
        time.sleep(0.05)
        beta.serviceAll()
        time.sleep(0.05)
        tymist.tick(tock=0.1)

    self.assertIs(beta.connector.accepted, True)
    self.assertIs(beta.connector.connected, True)
    self.assertIs(beta.connector.cutoff, False)

    self.assertEqual(len(alpha.servant.ixes), 1)
    self.assertEqual(len(alpha.reqs), 1)
    self.assertEqual(len(alpha.reps), 1)
    requestant = alpha.reqs.values()[0]
    self.assertEqual(requestant.method, request['method'])
    self.assertEqual(requestant.url, request['path'])
    self.assertEqual(requestant.headers, {'accept': 'application/json',
                                            'accept-encoding': 'identity',
                                            'content-length': '0',
                                            'host': 'localhost:6101'})


    #timed out while stream still open so no responses in .responses
    self.assertIs(beta.waited, True)
    self.assertIs(beta.respondent.ended, False)
    self.assertEqual(len(beta.responses), 0)
    self.assertIn('content-type', beta.respondent.headers)
    self.assertEqual(beta.respondent.headers['content-type'], 'text/event-stream')
    self.assertIn('transfer-encoding', beta.respondent.headers)
    self.assertEqual(beta.respondent.headers['transfer-encoding'], 'chunked')

    self.assertTrue(len(beta.events) >= 3)
    self.assertEqual(beta.respondent.retry, 1000)
    self.assertTrue(int(beta.respondent.leid) >= 2)
    event = beta.events.popleft()
    self.assertEqual(event, {'id': '0', 'name': '', 'data': 'START'})
    event = beta.events.popleft()
    self.assertEqual(event, {'id': '1', 'name': '', 'data': '1'})
    event = beta.events.popleft()
    self.assertEqual(event, {'id': '2', 'name': '', 'data': '2'})
    beta.events.clear()

    #keep going until ended
    tymer.restart(duration=1.5)
    while (not timer.expired):
        alpha.serviceAll()
        time.sleep(0.05)
        beta.serviceAll()
        time.sleep(0.05)
        tymist.tick(tock=0.1)

    self.assertTrue(len(beta.events) >= 3)
    self.assertEqual(beta.respondent.leid,  '9')
    self.assertEqual(beta.events[-2], {'id': '9', 'name': '', 'data': '9'})
    self.assertEqual(beta.events[-1], {'id': '9', 'name': '', 'data': 'END'})
    beta.events.clear()

    alpha.servant.closeAll()
    beta.connector.close()

    wireLogAlpha.close()
    wireLogBeta.close()


if __name__ == '__main__':
    pass