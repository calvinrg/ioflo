# -*- coding: utf-8 -*-
"""
Unittests for nonblocking module
"""

import sys
if sys.version > '3':
    xrange = range
if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

import os
import time
import tempfile
import shutil
import socket
import errno

try:
    import simplejson as json
except ImportError:
    import json

# Import ioflo libs
from ioflo.base.globaling import *
from ioflo.base.odicting import odict
#from ioflo.test import testing

from ioflo.aid import nonblocking
from ioflo.aid import httping
from ioflo.base.aiding import Timer, StoreTimer
from ioflo.base import storing

from ioflo.base.consoling import getConsole
console = getConsole()


from ioflo.aid import httping

def setUpModule():
    console.reinit(verbosity=console.Wordage.concise)

def tearDownModule():
    pass

class BasicTestCase(unittest.TestCase):
    """
    Test Case
    """

    def setUp(self):
        """

        """
        pass

    def tearDown(self):
        """

        """
        pass

    def testNonBlockingRequestEcho(self):
        """
        Test NonBlocking Http client
        """
        console.terse("{0}\n".format(self.testNonBlockingRequestEcho.__doc__))

        console.reinit(verbosity=console.Wordage.profuse)

        wireLogAlpha = nonblocking.WireLog(buffify=True, same=True)
        result = wireLogAlpha.reopen()

        wireLogBeta = nonblocking.WireLog(buffify=True,  same=True)
        result = wireLogBeta.reopen()

        alpha = nonblocking.Server(port = 6101, bufsize=131072, wlog=wireLogAlpha)
        self.assertIs(alpha.reopen(), True)
        self.assertEqual(alpha.ha, ('0.0.0.0', 6101))
        self.assertEqual(alpha.eha, ('127.0.0.1', 6101))

        beta = nonblocking.Outgoer(ha=alpha.eha, bufsize=131072, wlog=wireLogBeta)
        self.assertIs(beta.reopen(), True)
        self.assertIs(beta.accepted, False)
        self.assertIs(beta.connected, False)
        self.assertIs(beta.cutoff, False)

        console.terse("Connecting beta to server ...\n")
        while True:
            beta.serviceConnect()
            alpha.serviceConnects()
            if beta.connected and beta.ca in alpha.ixes:
                break
            time.sleep(0.05)

        self.assertIs(beta.accepted, True)
        self.assertIs(beta.connected, True)
        self.assertIs(beta.cutoff, False)
        self.assertEqual(beta.ca, beta.cs.getsockname())
        self.assertEqual(beta.ha, beta.cs.getpeername())
        self.assertEqual(alpha.eha, beta.ha)

        ixBeta = alpha.ixes[beta.ca]
        self.assertIsNotNone(ixBeta.ca)
        self.assertIsNotNone(ixBeta.cs)
        self.assertEqual(ixBeta.cs.getsockname(), beta.cs.getpeername())
        self.assertEqual(ixBeta.cs.getpeername(), beta.cs.getsockname())
        self.assertEqual(ixBeta.ca, beta.ca)
        self.assertEqual(ixBeta.ha, beta.ha)

        console.terse("{0}\n".format("Building Request ...\n"))
        host = u'127.0.0.1'
        port = 6101
        method = u'GET'
        path = u'/echo?name=fame'
        console.terse("{0} from  {1}:{2}{3} ...\n".format(method, host, port, path))
        headers = odict([(u'Accept', u'application/json')])
        request =  httping.Requester(host=host,
                                     port=port,
                                     method=method,
                                     path=path,
                                     headers=headers)
        msgOut = request.build()
        lines = [
                   b'GET /echo?name=fame HTTP/1.1',
                   b'Host: 127.0.0.1:6101',
                   b'Accept-Encoding: identity',
                   b'Content-Length: 0',
                   b'Accept: application/json',
                   b'',
                   b'',
                ]
        for i, line in enumerate(lines):
            self.assertEqual(line, request.lines[i])

        self.assertEqual(request.head, b'GET /echo?name=fame HTTP/1.1\r\nHost: 127.0.0.1:6101\r\nAccept-Encoding: identity\r\nContent-Length: 0\r\nAccept: application/json\r\n\r\n')
        self.assertEqual(msgOut, b'GET /echo?name=fame HTTP/1.1\r\nHost: 127.0.0.1:6101\r\nAccept-Encoding: identity\r\nContent-Length: 0\r\nAccept: application/json\r\n\r\n')

        console.terse("Beta requests to Alpha\n")
        beta.tx(msgOut)
        while beta.txes and not ixBeta.rxbs :
            beta.serviceTxes()
            time.sleep(0.05)
            alpha.serviceAllRxAllIx()
            time.sleep(0.05)
        msgIn = bytes(ixBeta.rxbs)
        self.assertEqual(msgIn, msgOut)
        ixBeta.clearRxbs()

        console.terse("Alpha responds to Beta\n")
        msgOut = b'HTTP/1.1 200 OK\r\nContent-Length: 122\r\nContent-Type: application/json\r\nDate: Thu, 30 Apr 2015 19:37:17 GMT\r\nServer: IoBook.local\r\n\r\n{"content": null, "query": {"name": "fame"}, "verb": "GET", "url": "http://127.0.0.1:8080/echo?name=fame", "action": null}'
        ixBeta.tx(msgOut)
        while ixBeta.txes or not beta.rxbs:
            alpha.serviceTxesAllIx()
            time.sleep(0.05)
            beta.serviceAllRx()
            time.sleep(0.05)
        msgIn = bytes(beta.rxbs)
        self.assertEqual(msgIn, msgOut)

        console.terse("Beta processes response \n")
        response = httping.Respondent(beta.rxbs, method=method)
        while response.parser:
            response.parse()

        self.assertEqual(bytes(response.body), b'{"content": null, "query": {"name": "fame"}, "verb": "GET", "url": "http://127.0.0.1:8080/echo?name=fame", "action": null}')
        self.assertEqual(len(beta.rxbs), 0)
        self.assertEqual(response.headers.items(), [('content-length', '122'),
                                                    ('content-type', 'application/json'),
                                                    ('date', 'Thu, 30 Apr 2015 19:37:17 GMT'),
                                                    ('server', 'IoBook.local')])

        alpha.close()
        beta.close()

        wireLogAlpha.close()
        wireLogBeta.close()
        console.reinit(verbosity=console.Wordage.concise)

    def testNonBlockingRequestStream(self):
        """
        Test NonBlocking Http client with SSE streaming server
        """
        console.terse("{0}\n".format(self.testNonBlockingRequestStream.__doc__))

        console.reinit(verbosity=console.Wordage.profuse)

        wireLogAlpha = nonblocking.WireLog(buffify=True, same=True)
        result = wireLogAlpha.reopen()

        wireLogBeta = nonblocking.WireLog(buffify=True, same=True)
        result = wireLogBeta.reopen()

        alpha = nonblocking.Server(port = 6101, bufsize=131072, wlog=wireLogAlpha)
        self.assertIs(alpha.reopen(), True)
        self.assertEqual(alpha.ha, ('0.0.0.0', 6101))
        self.assertEqual(alpha.eha, ('127.0.0.1', 6101))

        beta = nonblocking.Outgoer(ha=alpha.eha, bufsize=131072, wlog=wireLogBeta)
        self.assertIs(beta.reopen(), True)
        self.assertIs(beta.accepted, False)
        self.assertIs(beta.connected, False)
        self.assertIs(beta.cutoff, False)

        console.terse("Connecting beta to server ...\n")
        while True:
            beta.serviceConnect()
            alpha.serviceConnects()
            if beta.connected and beta.ca in alpha.ixes:
                break
            time.sleep(0.05)

        self.assertIs(beta.accepted, True)
        self.assertIs(beta.connected, True)
        self.assertIs(beta.cutoff, False)
        self.assertEqual(beta.ca, beta.cs.getsockname())
        self.assertEqual(beta.ha, beta.cs.getpeername())
        self.assertEqual(alpha.eha, beta.ha)

        ixBeta = alpha.ixes[beta.ca]
        self.assertIsNotNone(ixBeta.ca)
        self.assertIsNotNone(ixBeta.cs)
        self.assertEqual(ixBeta.cs.getsockname(), beta.cs.getpeername())
        self.assertEqual(ixBeta.cs.getpeername(), beta.cs.getsockname())
        self.assertEqual(ixBeta.ca, beta.ca)
        self.assertEqual(ixBeta.ha, beta.ha)

        console.terse("{0}\n".format("Building Request ...\n"))
        host = u'127.0.0.1'
        port = 6061
        method = u'GET'
        path = u'/stream'
        console.terse("{0} from  {1}:{2}{3} ...\n".format(method, host, port, path))
        headers = odict([(u'Accept', u'application/json')])
        request =  httping.Requester(host=host,
                                     port=port,
                                     method=method,
                                     path=path,
                                     headers=headers)
        msgOut = request.build()
        lines = [
                   b'GET /stream HTTP/1.1',
                   b'Host: 127.0.0.1:6061',
                   b'Accept-Encoding: identity',
                   b'Content-Length: 0',
                   b'Accept: application/json',
                   b'',
                   b'',
                ]
        for i, line in enumerate(lines):
            self.assertEqual(line, request.lines[i])

        self.assertEqual(request.head, b'GET /stream HTTP/1.1\r\nHost: 127.0.0.1:6061\r\nAccept-Encoding: identity\r\nContent-Length: 0\r\nAccept: application/json\r\n\r\n')
        self.assertEqual(msgOut, request.head)

        console.terse("Beta requests to Alpha\n")
        beta.tx(msgOut)
        while beta.txes and not ixBeta.rxbs :
            beta.serviceTxes()
            time.sleep(0.05)
            alpha.serviceAllRxAllIx()
            time.sleep(0.05)
        msgIn = bytes(ixBeta.rxbs)
        self.assertEqual(msgIn, msgOut)
        ixBeta.clearRxbs()

        console.terse("Alpha responds to Beta\n")
        lines = [
                        b'HTTP/1.0 200 OK\r\n',
                        b'Server: PasteWSGIServer/0.5 Python/2.7.9\r\n',
                        b'Date: Thu, 30 Apr 2015 21:35:25 GMT\r\n'
                        b'Content-Type: text/event-stream\r\n',
                        b'Cache-Control: no-cache\r\n',
                        b'Connection: close\r\n\r\n',
                    ]

        msgOut = b''.join(lines)
        ixBeta.tx(msgOut)
        while ixBeta.txes or not beta.rxbs:
            alpha.serviceTxesAllIx()
            time.sleep(0.05)
            beta.serviceAllRx()
            time.sleep(0.05)
        msgIn = bytes(beta.rxbs)
        self.assertEqual(msgIn, msgOut)

        console.terse("Beta processes response \n")
        response = httping.Respondent(beta.rxbs, method=method)

        lines =  [
                    b'retry: 1000\n\n',
                    b'data: START\n\n',
                    b'data: 1\n\n',
                    b'data: 2\n\n',
                    b'data: 3\n\n',
                    b'data: 4\n\n',
                 ]
        msgOut = b''.join(lines)
        ixBeta.tx(msgOut)
        timer = Timer(duration=0.5)
        while response.parser and not timer.expired:
            alpha.serviceTxesAllIx()
            response.parse()
            beta.serviceAllRx()
            time.sleep(0.01)

        if response.parser:
            response.parser.close()
            response.parser = None

        self.assertEqual(len(beta.rxbs), 0)
        self.assertEqual(response.eventSource.retry, 1000)
        self.assertEqual(response.retry, response.eventSource.retry)
        self.assertEqual(response.eventSource.leid, None)
        self.assertEqual(response.leid, response.eventSource.leid)
        self.assertTrue(len(response.events) > 2)
        event = response.events.popleft()
        self.assertEqual(event, {'id': None, 'name': '', 'data': 'START', 'json': None})
        event = response.events.popleft()
        self.assertEqual(event, {'id': None, 'name': '', 'data': '1', 'json': None})
        event = response.events.popleft()
        self.assertEqual(event, {'id': None, 'name': '', 'data': '2', 'json': None})
        self.assertTrue(len(response.body) == 0)
        self.assertTrue(len(response.eventSource.raw) == 0)

        alpha.close()
        beta.close()
        wireLogAlpha.close()
        wireLogBeta.close()
        console.reinit(verbosity=console.Wordage.concise)

    def testNonBlockingRequestStreamChunked(self):
        """
        Test NonBlocking Http client with SSE streaming server with transfer encoding (chunked)
        """
        console.terse("{0}\n".format(self.testNonBlockingRequestStreamChunked.__doc__))

        console.reinit(verbosity=console.Wordage.profuse)

        wireLogAlpha = nonblocking.WireLog(buffify=True, same=True)
        result = wireLogAlpha.reopen()

        wireLogBeta = nonblocking.WireLog(buffify=True, same=True)
        result = wireLogBeta.reopen()

        alpha = nonblocking.Server(port = 6101, bufsize=131072, wlog=wireLogAlpha)
        self.assertIs(alpha.reopen(), True)
        self.assertEqual(alpha.ha, ('0.0.0.0', 6101))
        self.assertEqual(alpha.eha, ('127.0.0.1', 6101))

        beta = nonblocking.Outgoer(ha=alpha.eha, bufsize=131072, wlog=wireLogBeta)
        self.assertIs(beta.reopen(), True)
        self.assertIs(beta.accepted, False)
        self.assertIs(beta.connected, False)
        self.assertIs(beta.cutoff, False)

        console.terse("Connecting beta to server ...\n")
        while True:
            beta.serviceConnect()
            alpha.serviceConnects()
            if beta.connected and beta.ca in alpha.ixes:
                break
            time.sleep(0.05)

        self.assertIs(beta.accepted, True)
        self.assertIs(beta.connected, True)
        self.assertIs(beta.cutoff, False)
        self.assertEqual(beta.ca, beta.cs.getsockname())
        self.assertEqual(beta.ha, beta.cs.getpeername())
        self.assertEqual(alpha.eha, beta.ha)

        ixBeta = alpha.ixes[beta.ca]
        self.assertIsNotNone(ixBeta.ca)
        self.assertIsNotNone(ixBeta.cs)
        self.assertEqual(ixBeta.cs.getsockname(), beta.cs.getpeername())
        self.assertEqual(ixBeta.cs.getpeername(), beta.cs.getsockname())
        self.assertEqual(ixBeta.ca, beta.ca)
        self.assertEqual(ixBeta.ha, beta.ha)

        console.terse("{0}\n".format("Building Request ...\n"))
        host = u'127.0.0.1'
        port = 6061
        method = u'GET'
        path = u'/stream'
        console.terse("{0} from  {1}:{2}{3} ...\n".format(method, host, port, path))
        headers = odict([(u'Accept', u'application/json')])
        request =  httping.Requester(host=host,
                                     port=port,
                                     method=method,
                                     path=path,
                                     headers=headers)
        msgOut = request.build()
        lines = [
                   b'GET /stream HTTP/1.1',
                   b'Host: 127.0.0.1:6061',
                   b'Accept-Encoding: identity',
                   b'Content-Length: 0',
                   b'Accept: application/json',
                   b'',
                   b'',
                ]
        for i, line in enumerate(lines):
            self.assertEqual(line, request.lines[i])

        self.assertEqual(request.head, b'GET /stream HTTP/1.1\r\nHost: 127.0.0.1:6061\r\nAccept-Encoding: identity\r\nContent-Length: 0\r\nAccept: application/json\r\n\r\n')
        self.assertEqual(msgOut, request.head)

        console.terse("Beta requests to Alpha\n")
        beta.tx(msgOut)
        while beta.txes and not ixBeta.rxbs :
            beta.serviceTxes()
            time.sleep(0.05)
            alpha.serviceAllRxAllIx()
            time.sleep(0.05)
        msgIn = bytes(ixBeta.rxbs)
        self.assertEqual(msgIn, msgOut)
        ixBeta.clearRxbs()

        console.terse("Alpha responds to Beta\n")
        lines = [
                        b'HTTP/1.1 200 OK\r\n',
                        b'Content-Type: text/event-stream\r\n',
                        b'Cache-Control: no-cache\r\n',
                        b'Transfer-Encoding: chunked\r\n',
                        b'Date: Thu, 30 Apr 2015 20:11:35 GMT\r\n',
                        b'Server: IoBook.local\r\n\r\n',
                    ]

        msgOut = b''.join(lines)
        ixBeta.tx(msgOut)
        while ixBeta.txes or not beta.rxbs:
            alpha.serviceTxesAllIx()
            time.sleep(0.05)
            beta.serviceAllRx()
            time.sleep(0.05)
        msgIn = bytes(beta.rxbs)
        self.assertEqual(msgIn, msgOut)

        console.terse("Beta processes response \n")
        response = httping.Respondent(beta.rxbs, method=method, wlog=wireLogBeta)

        lines =  [
                    b'd\r\nretry: 1000\n\n\r\n',
                    b'd\r\ndata: START\n\n\r\n',
                    b'9\r\ndata: 1\n\n\r\n',
                    b'9\r\ndata: 2\n\n\r\n',
                    b'9\r\ndata: 3\n\n\r\n',
                    b'9\r\ndata: 4\n\n\r\n',
                 ]
        msgOut = b''.join(lines)
        ixBeta.tx(msgOut)
        timer = Timer(duration=0.5)
        while response.parser and not timer.expired:
            alpha.serviceTxesAllIx()
            response.parse()
            beta.serviceAllRx()
            time.sleep(0.01)

        if response.parser:
            response.parser.close()
            response.parser = None

        self.assertEqual(len(beta.rxbs), 0)
        self.assertEqual(response.eventSource.retry, 1000)
        self.assertEqual(response.retry, response.eventSource.retry)
        self.assertEqual(response.eventSource.leid, None)
        self.assertEqual(response.leid, response.eventSource.leid)
        self.assertTrue(len(response.events) > 2)
        event = response.events.popleft()
        self.assertEqual(event, {'id': None, 'name': '', 'data': 'START', 'json': None})
        event = response.events.popleft()
        self.assertEqual(event, {'id': None, 'name': '', 'data': '1', 'json': None})
        event = response.events.popleft()
        self.assertEqual(event, {'id': None, 'name': '', 'data': '2', 'json': None})
        self.assertTrue(len(response.body) == 0)
        self.assertTrue(len(response.eventSource.raw) == 0)

        alpha.close()
        beta.close()
        wireLogAlpha.close()
        wireLogBeta.close()
        console.reinit(verbosity=console.Wordage.concise)

    def testNonBlockingRequestStreamFancy(self):
        """
        Test NonBlocking Http client to SSE server
        """
        console.terse("{0}\n".format(self.testNonBlockingRequestStreamFancy.__doc__))

        console.reinit(verbosity=console.Wordage.profuse)

        wireLogAlpha = nonblocking.WireLog(buffify=True, same=True)
        result = wireLogAlpha.reopen()

        wireLogBeta = nonblocking.WireLog(buffify=True, same=True)
        result = wireLogBeta.reopen()

        alpha = nonblocking.Server(port = 6101, bufsize=131072, wlog=wireLogAlpha)
        self.assertIs(alpha.reopen(), True)
        self.assertEqual(alpha.ha, ('0.0.0.0', 6101))
        self.assertEqual(alpha.eha, ('127.0.0.1', 6101))

        beta = nonblocking.Outgoer(ha=alpha.eha, bufsize=131072, wlog=wireLogBeta)
        self.assertIs(beta.reopen(), True)
        self.assertIs(beta.accepted, False)
        self.assertIs(beta.connected, False)
        self.assertIs(beta.cutoff, False)

        console.terse("Connecting beta to server ...\n")
        while True:
            beta.serviceConnect()
            alpha.serviceConnects()
            if beta.connected and beta.ca in alpha.ixes:
                break
            time.sleep(0.05)

        self.assertIs(beta.accepted, True)
        self.assertIs(beta.connected, True)
        self.assertIs(beta.cutoff, False)
        self.assertEqual(beta.ca, beta.cs.getsockname())
        self.assertEqual(beta.ha, beta.cs.getpeername())
        self.assertEqual(alpha.eha, beta.ha)

        ixBeta = alpha.ixes[beta.ca]
        self.assertIsNotNone(ixBeta.ca)
        self.assertIsNotNone(ixBeta.cs)
        self.assertEqual(ixBeta.cs.getsockname(), beta.cs.getpeername())
        self.assertEqual(ixBeta.cs.getpeername(), beta.cs.getsockname())
        self.assertEqual(ixBeta.ca, beta.ca)
        self.assertEqual(ixBeta.ha, beta.ha)

        console.terse("{0}\n".format("Building Request ...\n"))
        host = u'127.0.0.1'
        port = 6061
        method = u'GET'
        path = u'/fancy?idify=true;multiply=true'
        console.terse("{0} from  {1}:{2}{3} ...\n".format(method, host, port, path))
        headers = odict([(u'Accept', u'application/json')])
        request =  httping.Requester(host=host,
                                     port=port,
                                     method=method,
                                     path=path,
                                     headers=headers)
        msgOut = request.build()
        lines = [
                   b'GET /fancy?idify=true;multiply=true HTTP/1.1',
                   b'Host: 127.0.0.1:6061',
                   b'Accept-Encoding: identity',
                   b'Content-Length: 0',
                   b'Accept: application/json',
                   b'',
                   b'',
                ]
        for i, line in enumerate(lines):
            self.assertEqual(line, request.lines[i])

        self.assertEqual(request.head, b'GET /fancy?idify=true;multiply=true HTTP/1.1\r\nHost: 127.0.0.1:6061\r\nAccept-Encoding: identity\r\nContent-Length: 0\r\nAccept: application/json\r\n\r\n')
        self.assertEqual(msgOut, request.head)

        console.terse("Beta requests to Alpha\n")
        beta.tx(msgOut)
        while beta.txes and not ixBeta.rxbs :
            beta.serviceTxes()
            time.sleep(0.05)
            alpha.serviceAllRxAllIx()
            time.sleep(0.05)
        msgIn = bytes(ixBeta.rxbs)
        self.assertEqual(msgIn, msgOut)
        ixBeta.clearRxbs()

        console.terse("Alpha responds to Beta\n")
        lines = [
            b'HTTP/1.0 200 OK\r\n',
            b'Server: PasteWSGIServer/0.5 Python/2.7.9\r\n',
            b'Date: Thu, 30 Apr 2015 21:35:25 GMT\r\n'
            b'Content-Type: text/event-stream\r\n',
            b'Cache-Control: no-cache\r\n',
            b'Connection: close\r\n\r\n',
        ]

        msgOut = b''.join(lines)
        ixBeta.tx(msgOut)
        while ixBeta.txes or not beta.rxbs:
            alpha.serviceTxesAllIx()
            time.sleep(0.05)
            beta.serviceAllRx()
            time.sleep(0.05)
        msgIn = bytes(beta.rxbs)
        self.assertEqual(msgIn, msgOut)

        console.terse("Beta processes response \n")
        response = httping.Respondent(beta.rxbs, method=method, wlog=wireLogBeta)

        lines =  [
            b'retry: 1000\n\n',
            b'id: 0\ndata: START\n\n',
            b'id: 1\ndata: 1\ndata: 2\n\n',
            b'id: 2\ndata: 3\ndata: 4\n\n',
            b'id: 3\ndata: 5\ndata: 6\n\n',
            b'id: 4\ndata: 7\ndata: 8\n\n',
        ]
        msgOut = b''.join(lines)
        ixBeta.tx(msgOut)
        timer = Timer(duration=0.5)
        while response.parser and not timer.expired:
            alpha.serviceTxesAllIx()
            response.parse()
            beta.serviceAllRx()
            time.sleep(0.01)

        if response.parser:
            response.parser.close()
            response.parser = None

        self.assertEqual(len(beta.rxbs), 0)
        self.assertEqual(response.eventSource.retry, 1000)
        self.assertEqual(response.retry, response.eventSource.retry)
        self.assertTrue(int(response.eventSource.leid) >= 2)
        self.assertEqual(response.leid, response.eventSource.leid)
        self.assertTrue(len(response.events) > 2)
        event = response.events.popleft()
        self.assertEqual(event, {'id': '0', 'name': '', 'data': 'START', 'json': None})
        event = response.events.popleft()
        self.assertEqual(event, {'id': '1', 'name': '', 'data': '1\n2', 'json': None})
        event = response.events.popleft()
        self.assertEqual(event, {'id': '2', 'name': '', 'data': '3\n4', 'json': None})
        self.assertTrue(len(response.body) == 0)
        self.assertTrue(len(response.eventSource.raw) == 0)

        alpha.close()
        beta.close()

        wireLogAlpha.close()
        wireLogBeta.close()
        console.reinit(verbosity=console.Wordage.concise)

    def testNonBlockingRequestStreamFancyChunked(self):
        """
        Test NonBlocking Http client to server Fancy SSE with chunked transfer encoding
        """
        console.terse("{0}\n".format(self.testNonBlockingRequestStreamFancyChunked.__doc__))

        console.reinit(verbosity=console.Wordage.profuse)

        wireLogAlpha = nonblocking.WireLog(buffify=True, same=True)
        result = wireLogAlpha.reopen()

        wireLogBeta = nonblocking.WireLog(buffify=True, same=True)
        result = wireLogBeta.reopen()

        alpha = nonblocking.Server(port = 6101, bufsize=131072, wlog=wireLogAlpha)
        self.assertIs(alpha.reopen(), True)
        self.assertEqual(alpha.ha, ('0.0.0.0', 6101))
        self.assertEqual(alpha.eha, ('127.0.0.1', 6101))

        beta = nonblocking.Outgoer(ha=alpha.eha, bufsize=131072, wlog=wireLogBeta)
        self.assertIs(beta.reopen(), True)
        self.assertIs(beta.accepted, False)
        self.assertIs(beta.connected, False)
        self.assertIs(beta.cutoff, False)

        console.terse("Connecting beta to server ...\n")
        while True:
            beta.serviceConnect()
            alpha.serviceConnects()
            if beta.connected and beta.ca in alpha.ixes:
                break
            time.sleep(0.05)

        self.assertIs(beta.accepted, True)
        self.assertIs(beta.connected, True)
        self.assertIs(beta.cutoff, False)
        self.assertEqual(beta.ca, beta.cs.getsockname())
        self.assertEqual(beta.ha, beta.cs.getpeername())
        self.assertEqual(alpha.eha, beta.ha)

        ixBeta = alpha.ixes[beta.ca]
        self.assertIsNotNone(ixBeta.ca)
        self.assertIsNotNone(ixBeta.cs)
        self.assertEqual(ixBeta.cs.getsockname(), beta.cs.getpeername())
        self.assertEqual(ixBeta.cs.getpeername(), beta.cs.getsockname())
        self.assertEqual(ixBeta.ca, beta.ca)
        self.assertEqual(ixBeta.ha, beta.ha)

        console.terse("{0}\n".format("Building Request ...\n"))
        host = u'127.0.0.1'
        port = 6061
        method = u'GET'
        path = u'/fancy?idify=true;multiply=true'
        console.terse("{0} from  {1}:{2}{3} ...\n".format(method, host, port, path))
        headers = odict([(u'Accept', u'application/json')])
        request =  httping.Requester(host=host,
                                     port=port,
                                     method=method,
                                     path=path,
                                     headers=headers)

        msgOut = request.build()
        lines = [
                   b'GET /fancy?idify=true;multiply=true HTTP/1.1',
                   b'Host: 127.0.0.1:6061',
                   b'Accept-Encoding: identity',
                   b'Content-Length: 0',
                   b'Accept: application/json',
                   b'',
                   b'',
                ]
        for i, line in enumerate(lines):
            self.assertEqual(line, request.lines[i])

        self.assertEqual(request.head, b'GET /fancy?idify=true;multiply=true HTTP/1.1\r\nHost: 127.0.0.1:6061\r\nAccept-Encoding: identity\r\nContent-Length: 0\r\nAccept: application/json\r\n\r\n')
        self.assertEqual(msgOut, request.head)

        console.terse("Beta requests to Alpha\n")
        beta.tx(msgOut)
        while beta.txes and not ixBeta.rxbs :
            beta.serviceTxes()
            time.sleep(0.05)
            alpha.serviceAllRxAllIx()
            time.sleep(0.05)
        msgIn = bytes(ixBeta.rxbs)
        self.assertEqual(msgIn, msgOut)
        ixBeta.clearRxbs()

        console.terse("Alpha responds to Beta\n")
        lines = [
            b'HTTP/1.1 200 OK\r\n',
            b'Content-Type: text/event-stream\r\n',
            b'Cache-Control: no-cache\r\n',
            b'Transfer-Encoding: chunked\r\n',
            b'Date: Thu, 30 Apr 2015 22:11:53 GMT\r\n',
            b'Server: IoBook.local\r\n\r\n',
        ]

        msgOut = b''.join(lines)
        ixBeta.tx(msgOut)
        while ixBeta.txes or not beta.rxbs:
            alpha.serviceTxesAllIx()
            time.sleep(0.05)
            beta.serviceAllRx()
            time.sleep(0.05)
        msgIn = bytes(beta.rxbs)
        self.assertEqual(msgIn, msgOut)

        console.terse("Beta processes response \n")
        response = httping.Respondent(beta.rxbs, method=method, wlog=wireLogBeta)

        lines =  [
            b'd\r\nretry: 1000\n\n\r\n',
            b'6\r\nid: 0\n\r\n',
            b'd\r\ndata: START\n\n\r\n',
            b'6\r\nid: 1\n\r\n',
            b'8\r\ndata: 1\n\r\n',
            b'8\r\ndata: 2\n\r\n',
            b'1\r\n\n\r\n',
            b'6\r\nid: 2\n\r\n',
            b'8\r\ndata: 3\n\r\n',
            b'8\r\ndata: 4\n\r\n',
            b'1\r\n\n\r\n',
            b'6\r\nid: 3\n\r\n',
            b'8\r\ndata: 5\n\r\n',
            b'8\r\ndata: 6\n\r\n',
            b'1\r\n\n\r\n',
            b'6\r\nid: 4\n\r\n8\r\ndata: 7\n\r\n8\r\ndata: 8\n\r\n',
            b'1\r\n\n\r\n',
        ]
        msgOut = b''.join(lines)
        ixBeta.tx(msgOut)
        timer = Timer(duration=0.5)
        while response.parser and not timer.expired:
            alpha.serviceTxesAllIx()
            response.parse()
            beta.serviceAllRx()
            time.sleep(0.01)

        if response.parser:
            response.parser.close()
            response.parser = None

        self.assertEqual(len(beta.rxbs), 0)
        self.assertEqual(response.eventSource.retry, 1000)
        self.assertEqual(response.retry, response.eventSource.retry)
        self.assertTrue(int(response.eventSource.leid) >= 2)
        self.assertEqual(response.leid, response.eventSource.leid)
        self.assertTrue(len(response.events) > 2)
        event = response.events.popleft()
        self.assertEqual(event, {'id': '0', 'name': '', 'data': 'START', 'json': None})
        event = response.events.popleft()
        self.assertEqual(event, {'id': '1', 'name': '', 'data': '1\n2', 'json': None})
        event = response.events.popleft()
        self.assertEqual(event, {'id': '2', 'name': '', 'data': '3\n4', 'json': None})
        self.assertTrue(len(response.body) == 0)
        self.assertTrue(len(response.eventSource.raw) == 0)

        alpha.close()
        beta.close()

        wireLogAlpha.close()
        wireLogBeta.close()
        console.reinit(verbosity=console.Wordage.concise)

    def testNonBlockingRequestStreamFancyJson(self):
        """
        Test NonBlocking Http client to server Fancy SSE with chunked transfer encoding
        """
        console.terse("{0}\n".format(self.testNonBlockingRequestStreamFancyJson.__doc__))

        console.reinit(verbosity=console.Wordage.profuse)

        wireLogAlpha = nonblocking.WireLog(buffify=True, same=True)
        result = wireLogAlpha.reopen()

        wireLogBeta = nonblocking.WireLog(buffify=True, same=True)
        result = wireLogBeta.reopen()

        alpha = nonblocking.Server(port = 6101, bufsize=131072, wlog=wireLogAlpha)
        self.assertIs(alpha.reopen(), True)
        self.assertEqual(alpha.ha, ('0.0.0.0', 6101))
        self.assertEqual(alpha.eha, ('127.0.0.1', 6101))

        beta = nonblocking.Outgoer(ha=alpha.eha, bufsize=131072, wlog=wireLogBeta)
        self.assertIs(beta.reopen(), True)
        self.assertIs(beta.accepted, False)
        self.assertIs(beta.connected, False)
        self.assertIs(beta.cutoff, False)

        console.terse("Connecting beta to server ...\n")
        while True:
            beta.serviceConnect()
            alpha.serviceConnects()
            if beta.connected and beta.ca in alpha.ixes:
                break
            time.sleep(0.05)

        self.assertIs(beta.accepted, True)
        self.assertIs(beta.connected, True)
        self.assertIs(beta.cutoff, False)
        self.assertEqual(beta.ca, beta.cs.getsockname())
        self.assertEqual(beta.ha, beta.cs.getpeername())
        self.assertEqual(alpha.eha, beta.ha)

        ixBeta = alpha.ixes[beta.ca]
        self.assertIsNotNone(ixBeta.ca)
        self.assertIsNotNone(ixBeta.cs)
        self.assertEqual(ixBeta.cs.getsockname(), beta.cs.getpeername())
        self.assertEqual(ixBeta.cs.getpeername(), beta.cs.getsockname())
        self.assertEqual(ixBeta.ca, beta.ca)
        self.assertEqual(ixBeta.ha, beta.ha)

        console.terse("{0}\n".format("Building Request ...\n"))
        host = u'127.0.0.1'
        port = 6061
        method = u'GET'
        path = u'/fancy?idify=true;jsonify=true'
        console.terse("{0} from  {1}:{2}{3} ...\n".format(method, host, port, path))
        headers = odict([(u'Accept', u'application/json')])
        request =  httping.Requester(host=host,
                                         port=port,
                                         method=method,
                                         path=path,
                                         headers=headers)
        msgOut = request.build()
        lines = [
            b'GET /fancy?idify=true;jsonify=true HTTP/1.1',
            b'Host: 127.0.0.1:6061',
            b'Accept-Encoding: identity',
            b'Content-Length: 0',
            b'Accept: application/json',
            b'',
            b'',
        ]
        for i, line in enumerate(lines):
            self.assertEqual(line, request.lines[i])

        self.assertEqual(request.head, b'GET /fancy?idify=true;jsonify=true HTTP/1.1\r\nHost: 127.0.0.1:6061\r\nAccept-Encoding: identity\r\nContent-Length: 0\r\nAccept: application/json\r\n\r\n')
        self.assertEqual(msgOut, request.head)

        console.terse("Beta requests to Alpha\n")
        beta.tx(msgOut)
        while beta.txes and not ixBeta.rxbs :
            beta.serviceTxes()
            time.sleep(0.05)
            alpha.serviceAllRxAllIx()
            time.sleep(0.05)
        msgIn = bytes(ixBeta.rxbs)
        self.assertEqual(msgIn, msgOut)
        ixBeta.clearRxbs()

        console.terse("Alpha responds to Beta\n")
        lines = [
            b'HTTP/1.0 200 OK\r\n',
            b'Server: PasteWSGIServer/0.5 Python/2.7.9\r\n',
            b'Date: Thu, 30 Apr 2015 21:35:25 GMT\r\n'
            b'Content-Type: text/event-stream\r\n',
            b'Cache-Control: no-cache\r\n',
            b'Connection: close\r\n\r\n',
        ]

        msgOut = b''.join(lines)
        ixBeta.tx(msgOut)
        while ixBeta.txes or not beta.rxbs:
            alpha.serviceTxesAllIx()
            time.sleep(0.05)
            beta.serviceAllRx()
            time.sleep(0.05)
        msgIn = bytes(beta.rxbs)
        self.assertEqual(msgIn, msgOut)

        console.terse("Beta processes response \n")
        response = httping.Respondent(beta.rxbs,
                                      method=method,
                                      jsoned=True,
                                      wlog=wireLogBeta,
                                      )

        lines =  [
            b'retry: 1000\n\n',
            b'id: 0\ndata: START\n\n',
            b'id: 1\ndata: {"count":1}\n\n',
            b'id: 2\n',
            b'data: {"count":2}\n\n',
            b'id: 3\ndata: {"count":3}\n\n',
            b'id: 4\ndata: {"count":4}\n\n',
        ]
        msgOut = b''.join(lines)
        ixBeta.tx(msgOut)
        timer = Timer(duration=0.5)
        while response.parser and not timer.expired:
            alpha.serviceTxesAllIx()
            response.parse()
            beta.serviceAllRx()
            time.sleep(0.01)

        if response.parser:
            response.parser.close()
            response.parser = None

        self.assertEqual(len(beta.rxbs), 0)
        self.assertEqual(response.eventSource.retry, 1000)
        self.assertEqual(response.retry, response.eventSource.retry)
        self.assertTrue(int(response.eventSource.leid) >= 2)
        self.assertEqual(response.leid, response.eventSource.leid)
        self.assertTrue(len(response.events) > 2)
        event = response.events.popleft()
        self.assertEqual(event, {'id': '0', 'name': '', 'data': 'START', 'json': None})
        event = response.events.popleft()
        self.assertEqual(event, {'id': '1', 'name': '', 'data': None, 'json': {'count': 1}})
        event = response.events.popleft()
        self.assertEqual(event, {'id': '2', 'name': '', 'data': None, 'json': {'count': 2}})
        self.assertTrue(len(response.body) == 0)
        self.assertTrue(len(response.eventSource.raw) == 0)

        alpha.close()
        beta.close()

        wireLogAlpha.close()
        wireLogBeta.close()
        console.reinit(verbosity=console.Wordage.concise)

    def testNonBlockingRequestStreamFancyJsonChunked(self):
        """
        Test NonBlocking Http client to server Fancy SSE with chunked transfer encoding
        """
        console.terse("{0}\n".format(self.testNonBlockingRequestStreamFancyJsonChunked.__doc__))

        console.reinit(verbosity=console.Wordage.profuse)

        wireLogAlpha = nonblocking.WireLog(buffify=True, same=True)
        result = wireLogAlpha.reopen()

        wireLogBeta = nonblocking.WireLog(buffify=True, same=True)
        result = wireLogBeta.reopen()

        alpha = nonblocking.Server(port = 6101, bufsize=131072, wlog=wireLogAlpha)
        self.assertIs(alpha.reopen(), True)
        self.assertEqual(alpha.ha, ('0.0.0.0', 6101))
        self.assertEqual(alpha.eha, ('127.0.0.1', 6101))

        beta = nonblocking.Outgoer(ha=alpha.eha, bufsize=131072, wlog=wireLogBeta)
        self.assertIs(beta.reopen(), True)
        self.assertIs(beta.accepted, False)
        self.assertIs(beta.connected, False)
        self.assertIs(beta.cutoff, False)

        console.terse("Connecting beta to server ...\n")
        while True:
            beta.serviceConnect()
            alpha.serviceConnects()
            if beta.accepted and beta.ca in alpha.ixes:
                break
            time.sleep(0.05)

        self.assertIs(beta.accepted, True)
        self.assertIs(beta.connected, True)
        self.assertIs(beta.cutoff, False)
        self.assertEqual(beta.ca, beta.cs.getsockname())
        self.assertEqual(beta.ha, beta.cs.getpeername())
        self.assertEqual(alpha.eha, beta.ha)

        ixBeta = alpha.ixes[beta.ca]
        self.assertIsNotNone(ixBeta.ca)
        self.assertIsNotNone(ixBeta.cs)
        self.assertEqual(ixBeta.cs.getsockname(), beta.cs.getpeername())
        self.assertEqual(ixBeta.cs.getpeername(), beta.cs.getsockname())
        self.assertEqual(ixBeta.ca, beta.ca)
        self.assertEqual(ixBeta.ha, beta.ha)

        console.terse("{0}\n".format("Building Request ...\n"))
        host = u'127.0.0.1'
        port = 6061
        method = u'GET'
        path = u'/fancy?idify=true;jsonify=true'
        console.terse("{0} from  {1}:{2}{3} ...\n".format(method, host, port, path))
        headers = odict([(u'Accept', u'application/json')])
        request =  httping.Requester(host=host,
                                         port=port,
                                         method=method,
                                         path=path,
                                         headers=headers)
        msgOut = request.build()
        lines = [
            b'GET /fancy?idify=true;jsonify=true HTTP/1.1',
            b'Host: 127.0.0.1:6061',
            b'Accept-Encoding: identity',
            b'Content-Length: 0',
            b'Accept: application/json',
            b'',
            b'',
        ]
        for i, line in enumerate(lines):
            self.assertEqual(line, request.lines[i])

        self.assertEqual(request.head, b'GET /fancy?idify=true;jsonify=true HTTP/1.1\r\nHost: 127.0.0.1:6061\r\nAccept-Encoding: identity\r\nContent-Length: 0\r\nAccept: application/json\r\n\r\n')
        self.assertEqual(msgOut, request.head)

        console.terse("Beta requests to Alpha\n")
        beta.tx(msgOut)
        while beta.txes and not ixBeta.rxbs :
            beta.serviceTxes()
            time.sleep(0.05)
            alpha.serviceAllRxAllIx()
            time.sleep(0.05)
        msgIn = bytes(ixBeta.rxbs)
        self.assertEqual(msgIn, msgOut)
        ixBeta.clearRxbs()

        console.terse("Alpha responds to Beta\n")
        lines = [
            b'HTTP/1.1 200 OK\r\n',
            b'Content-Type: text/event-stream\r\n',
            b'Cache-Control: no-cache\r\n',
            b'Transfer-Encoding: chunked\r\n',
            b'Date: Thu, 30 Apr 2015 22:11:53 GMT\r\n',
            b'Server: IoBook.local\r\n\r\n',
        ]

        msgOut = b''.join(lines)
        ixBeta.tx(msgOut)
        while ixBeta.txes or not beta.rxbs:
            alpha.serviceTxesAllIx()
            time.sleep(0.05)
            beta.serviceAllRx()
            time.sleep(0.05)
        msgIn = bytes(beta.rxbs)
        self.assertEqual(msgIn, msgOut)

        console.terse("Beta processes response \n")
        response = httping.Respondent(beta.rxbs,
                                      method=method,
                                      jsoned=True,
                                      wlog=wireLogBeta,)

        lines =  [
            b'd\r\nretry: 1000\n\n\r\n',
            b'6\r\nid: 0\n\r\n'
            b'd\r\ndata: START\n\n\r\n',
            b'6\r\nid: 1\n\r\n',
            b'12\r\ndata: {"count":1}\n\r\n',
            b'1\r\n\n\r\n',
            b'6\r\nid: 2\n\r\n12\r\ndata: {"count":2}\n\r\n1\r\n\n\r\n',
            b'6\r\nid: 3\n\r\n12\r\ndata: {"count":3}\n\r\n1\r\n\n\r\n',
            b'6\r\nid: 4\n\r\n12\r\ndata: {"count":4}\n\r\n1\r\n\n\r\n',
        ]
        msgOut = b''.join(lines)
        ixBeta.tx(msgOut)
        timer = Timer(duration=0.5)
        while response.parser and not timer.expired:
            alpha.serviceTxesAllIx()
            response.parse()
            beta.serviceAllRx()
            time.sleep(0.01)

        if response.parser:
            response.parser.close()
            response.parser = None

        self.assertEqual(len(beta.rxbs), 0)
        self.assertEqual(response.eventSource.retry, 1000)
        self.assertEqual(response.retry, response.eventSource.retry)
        self.assertTrue(int(response.eventSource.leid) >= 2)
        self.assertEqual(response.leid, response.eventSource.leid)
        self.assertTrue(len(response.events) > 2)
        event = response.events.popleft()
        self.assertEqual(event, {'id': '0', 'name': '', 'data': 'START', 'json': None})
        event = response.events.popleft()
        self.assertEqual(event, {'id': '1', 'name': '', 'data': None, 'json': {'count': 1}})
        event = response.events.popleft()
        self.assertEqual(event, {'id': '2', 'name': '', 'data': None, 'json': {'count': 2}})
        self.assertTrue(len(response.body) == 0)
        self.assertTrue(len(response.eventSource.raw) == 0)

        alpha.close()
        beta.close()

        wireLogAlpha.close()
        wireLogBeta.close()
        console.reinit(verbosity=console.Wordage.concise)

    def testNonBlockingRequestEchoTLS(self):
        """
        Test NonBlocking HTTPS (TLS/SSL) client
        """
        console.terse("{0}\n".format(self.testNonBlockingRequestEchoTLS.__doc__))

        console.reinit(verbosity=console.Wordage.profuse)

        wireLogAlpha = nonblocking.WireLog(buffify=True, same=True)
        result = wireLogAlpha.reopen()

        wireLogBeta = nonblocking.WireLog(buffify=True,  same=True)
        result = wireLogBeta.reopen()

        serverKeypath = '/etc/pki/tls/certs/server_key.pem'  # local server private key
        serverCertpath = '/etc/pki/tls/certs/server_cert.pem'  # local server public cert
        clientCafilepath = '/etc/pki/tls/certs/client.pem' # remote client public cert

        clientKeypath = '/etc/pki/tls/certs/client_key.pem'  # local client private key
        clientCertpath = '/etc/pki/tls/certs/client_cert.pem'  # local client public cert
        serverCafilepath = '/etc/pki/tls/certs/server.pem' # remote server public cert

        alpha = nonblocking.ServerTls(host='localhost',
                                      port = 6101,
                                      bufsize=131072,
                                      wlog=wireLogAlpha,
                                      context=None,
                                      version=None,
                                      certify=None,
                                      keypath=serverKeypath,
                                      certpath=serverCertpath,
                                      cafilepath=clientCafilepath,
                                      )
        self.assertIs(alpha.reopen(), True)
        self.assertEqual(alpha.ha, ('127.0.0.1', 6101))
        self.assertEqual(alpha.eha, ('127.0.0.1', 6101))

        serverCertCommonName = 'localhost' # match hostname uses servers's cert commonname

        beta = nonblocking.OutgoerTls(ha=alpha.ha,
                                      bufsize=131072,
                                      wlog=wireLogBeta,
                                      context=None,
                                      version=None,
                                      certify=None,
                                      hostify=None,
                                      certedhost=serverCertCommonName,
                                      keypath=clientKeypath,
                                      certpath=clientCertpath,
                                      cafilepath=serverCafilepath,
                                      )
        self.assertIs(beta.reopen(), True)
        self.assertIs(beta.accepted, False)
        self.assertIs(beta.connected, False)
        self.assertIs(beta.cutoff, False)

        console.terse("Connecting  and Handshaking beta to alpha\n")
        while True:
            beta.serviceConnect()
            alpha.serviceConnects()
            if beta.connected and len(alpha.ixes) >= 1:
                break
            time.sleep(0.01)

        self.assertIs(beta.accepted, True)
        self.assertIs(beta.connected, True)
        self.assertIs(beta.cutoff, False)
        self.assertEqual(beta.ca, beta.cs.getsockname())
        self.assertEqual(beta.ha, beta.cs.getpeername())
        self.assertIs(beta.connected, True)

        ixBeta = alpha.ixes[beta.ca]
        self.assertIsNotNone(ixBeta.ca)
        self.assertIsNotNone(ixBeta.cs)
        self.assertEqual(ixBeta.cs.getsockname(), beta.cs.getpeername())
        self.assertEqual(ixBeta.cs.getpeername(), beta.cs.getsockname())
        self.assertEqual(ixBeta.ca, beta.ca)
        self.assertEqual(ixBeta.ha, beta.ha)

        console.terse("{0}\n".format("Building Request ...\n"))
        host = u'127.0.0.1'
        port = 6061
        method = u'GET'
        path = u'/echo?name=fame'
        console.terse("{0} from  {1}:{2}{3} ...\n".format(method, host, port, path))
        headers = odict([(u'Accept', u'application/json')])
        request =  httping.Requester(host=host,
                                     port=port,
                                     method=method,
                                     path=path,
                                     headers=headers)
        msgOut = request.build()
        lines = [
                   b'GET /echo?name=fame HTTP/1.1',
                   b'Host: 127.0.0.1:6061',
                   b'Accept-Encoding: identity',
                   b'Content-Length: 0',
                   b'Accept: application/json',
                   b'',
                   b'',
                ]
        for i, line in enumerate(lines):
            self.assertEqual(line, request.lines[i])

        self.assertEqual(request.head, b'GET /echo?name=fame HTTP/1.1\r\nHost: 127.0.0.1:6061\r\nAccept-Encoding: identity\r\nContent-Length: 0\r\nAccept: application/json\r\n\r\n')
        self.assertEqual(msgOut, b'GET /echo?name=fame HTTP/1.1\r\nHost: 127.0.0.1:6061\r\nAccept-Encoding: identity\r\nContent-Length: 0\r\nAccept: application/json\r\n\r\n')

        console.terse("Beta requests to Alpha\n")
        beta.tx(msgOut)
        while beta.txes and not ixBeta.rxbs :
            beta.serviceTxes()
            time.sleep(0.05)
            alpha.serviceAllRxAllIx()
            time.sleep(0.05)
        msgIn = bytes(ixBeta.rxbs)
        self.assertEqual(msgIn, msgOut)
        ixBeta.clearRxbs()

        console.terse("Alpha responds to Beta\n")
        msgOut = b'HTTP/1.1 200 OK\r\nContent-Length: 122\r\nContent-Type: application/json\r\nDate: Thu, 30 Apr 2015 19:37:17 GMT\r\nServer: IoBook.local\r\n\r\n{"content": null, "query": {"name": "fame"}, "verb": "GET", "url": "http://127.0.0.1:8080/echo?name=fame", "action": null}'
        ixBeta.tx(msgOut)
        while ixBeta.txes or not beta.rxbs:
            alpha.serviceTxesAllIx()
            time.sleep(0.05)
            beta.serviceAllRx()
            time.sleep(0.05)
        msgIn = bytes(beta.rxbs)
        self.assertEqual(msgIn, msgOut)

        console.terse("Beta processes response \n")
        response = httping.Respondent(beta.rxbs, method=method)
        while response.parser:
            response.parse()

        self.assertEqual(bytes(response.body), b'{"content": null, "query": {"name": "fame"}, "verb": "GET", "url": "http://127.0.0.1:8080/echo?name=fame", "action": null}')
        self.assertEqual(len(beta.rxbs), 0)
        self.assertEqual(response.headers.items(), [('content-length', '122'),
                                                    ('content-type', 'application/json'),
                                                    ('date', 'Thu, 30 Apr 2015 19:37:17 GMT'),
                                                    ('server', 'IoBook.local')])

        alpha.close()
        beta.close()

        wireLogAlpha.close()
        wireLogBeta.close()
        console.reinit(verbosity=console.Wordage.concise)


    def testPatronRequestEcho(self):
        """
        Test Patron request echo non blocking
        """
        console.terse("{0}\n".format(self.testPatronRequestEcho.__doc__))

        console.reinit(verbosity=console.Wordage.profuse)

        wireLogAlpha = nonblocking.WireLog(buffify=True, same=True)
        result = wireLogAlpha.reopen()

        alpha = nonblocking.Server(port = 6101, bufsize=131072, wlog=wireLogAlpha)
        self.assertIs(alpha.reopen(), True)
        self.assertEqual(alpha.ha, ('0.0.0.0', 6101))
        self.assertEqual(alpha.eha, ('127.0.0.1', 6101))

        console.terse("{0}\n".format("Building Connector ...\n"))

        wireLogBeta = nonblocking.WireLog(buffify=True,  same=True)
        result = wireLogBeta.reopen()
        host = alpha.eha[0]
        port = alpha.eha[1]
        method = u'GET'
        path = u'/echo?name=fame'
        headers = odict([(u'Accept', u'application/json')])


        beta = httping.Patron(bufsize=131072,
                                     wlog=wireLogBeta,
                                     host=host,
                                     port=port,
                                     method=method,
                                     path=path,
                                     headers=headers,
                                     )

        self.assertIs(beta.connector.reopen(), True)
        self.assertIs(beta.connector.accepted, False)
        self.assertIs(beta.connector.connected, False)
        self.assertIs(beta.connector.cutoff, False)

        console.terse("Connecting beta to server ...\n")
        while True:
            beta.connector.serviceConnect()
            alpha.serviceConnects()
            if beta.connector.connected and beta.connector.ca in alpha.ixes:
                break
            time.sleep(0.05)

        self.assertIs(beta.connector.accepted, True)
        self.assertIs(beta.connector.connected, True)
        self.assertIs(beta.connector.cutoff, False)
        self.assertEqual(beta.connector.ca, beta.connector.cs.getsockname())
        self.assertEqual(beta.connector.ha, beta.connector.cs.getpeername())
        self.assertEqual(alpha.eha, beta.connector.ha)

        ixBeta = alpha.ixes[beta.connector.ca]
        self.assertIsNotNone(ixBeta.ca)
        self.assertIsNotNone(ixBeta.cs)
        self.assertEqual(ixBeta.cs.getsockname(), beta.connector.cs.getpeername())
        self.assertEqual(ixBeta.cs.getpeername(), beta.connector.cs.getsockname())
        self.assertEqual(ixBeta.ca, beta.connector.ca)
        self.assertEqual(ixBeta.ha, beta.connector.ha)

        msgOut = beta.requester.build()
        lines = [
                   b'GET /echo?name=fame HTTP/1.1',
                   b'Host: 127.0.0.1:6101',
                   b'Accept-Encoding: identity',
                   b'Content-Length: 0',
                   b'Accept: application/json',
                   b'',
                   b'',
                ]
        for i, line in enumerate(lines):
            self.assertEqual(line, beta.requester.lines[i])

        self.assertEqual(beta.requester.head, b'GET /echo?name=fame HTTP/1.1\r\nHost: 127.0.0.1:6101\r\nAccept-Encoding: identity\r\nContent-Length: 0\r\nAccept: application/json\r\n\r\n')
        self.assertEqual(msgOut, b'GET /echo?name=fame HTTP/1.1\r\nHost: 127.0.0.1:6101\r\nAccept-Encoding: identity\r\nContent-Length: 0\r\nAccept: application/json\r\n\r\n')

        console.terse("Beta requests to Alpha\n")
        console.terse("{0} from  {1}:{2}{3} ...\n".format(method, host, port, path))
        beta.connector.tx(msgOut)
        while beta.connector.txes and not ixBeta.rxbs :
            beta.connector.serviceTxes()
            time.sleep(0.05)
            alpha.serviceAllRxAllIx()
            time.sleep(0.05)
        msgIn = bytes(ixBeta.rxbs)
        self.assertEqual(msgIn, msgOut)
        ixBeta.clearRxbs()

        console.terse("Alpha responds to Beta\n")
        msgOut = b'HTTP/1.1 200 OK\r\nContent-Length: 122\r\nContent-Type: application/json\r\nDate: Thu, 30 Apr 2015 19:37:17 GMT\r\nServer: IoBook.local\r\n\r\n{"content": null, "query": {"name": "fame"}, "verb": "GET", "url": "http://127.0.0.1:8080/echo?name=fame", "action": null}'
        ixBeta.tx(msgOut)
        while ixBeta.txes or not beta.connector.rxbs:
            alpha.serviceTxesAllIx()
            time.sleep(0.05)
            beta.connector.serviceAllRx()
            time.sleep(0.05)
        msgIn = bytes(beta.connector.rxbs)
        self.assertEqual(msgIn, msgOut)

        console.terse("Beta processes response \n")

        while beta.respondent.parser:
            beta.respondent.parse()

        self.assertEqual(bytes(beta.respondent.body), b'{"content": null, "query": {"name": "fame"}, "verb": "GET", "url": "http://127.0.0.1:8080/echo?name=fame", "action": null}')
        self.assertEqual(len(beta.connector.rxbs), 0)
        self.assertEqual(beta.respondent.headers.items(), [('content-length', '122'),
                                                    ('content-type', 'application/json'),
                                                    ('date', 'Thu, 30 Apr 2015 19:37:17 GMT'),
                                                    ('server', 'IoBook.local')])

        alpha.close()
        beta.connector.close()

        wireLogAlpha.close()
        wireLogBeta.close()
        console.reinit(verbosity=console.Wordage.concise)


    def testPatronServiceEcho(self):
        """
        Test Patron service request response of echo non blocking
        """
        console.terse("{0}\n".format(self.testPatronServiceEcho.__doc__))

        console.reinit(verbosity=console.Wordage.profuse)

        wireLogAlpha = nonblocking.WireLog(buffify=True, same=True)
        result = wireLogAlpha.reopen()

        alpha = nonblocking.Server(port = 6101, bufsize=131072, wlog=wireLogAlpha)
        self.assertIs(alpha.reopen(), True)
        self.assertEqual(alpha.ha, ('0.0.0.0', 6101))
        self.assertEqual(alpha.eha, ('127.0.0.1', 6101))

        console.terse("{0}\n".format("Building Connector ...\n"))

        wireLogBeta = nonblocking.WireLog(buffify=True,  same=True)
        result = wireLogBeta.reopen()
        host = alpha.eha[0]
        port = alpha.eha[1]
        method = u'GET'
        path = u'/echo?name=fame'
        headers = odict([(u'Accept', u'application/json')])


        beta = httping.Patron(bufsize=131072,
                              wlog=wireLogBeta,
                              host=host,
                              port=port,
                              method=method,
                              path=path,
                              headers=headers,
                              )

        self.assertIs(beta.connector.reopen(), True)
        self.assertIs(beta.connector.accepted, False)
        self.assertIs(beta.connector.connected, False)
        self.assertIs(beta.connector.cutoff, False)

        console.terse("Connecting beta to server ...\n")
        while True:
            beta.connector.serviceConnect()
            alpha.serviceConnects()
            if beta.connector.connected and beta.connector.ca in alpha.ixes:
                break
            time.sleep(0.05)

        self.assertIs(beta.connector.accepted, True)
        self.assertIs(beta.connector.connected, True)
        self.assertIs(beta.connector.cutoff, False)
        self.assertEqual(beta.connector.ca, beta.connector.cs.getsockname())
        self.assertEqual(beta.connector.ha, beta.connector.cs.getpeername())
        self.assertEqual(alpha.eha, beta.connector.ha)

        ixBeta = alpha.ixes[beta.connector.ca]
        self.assertIsNotNone(ixBeta.ca)
        self.assertIsNotNone(ixBeta.cs)
        self.assertEqual(ixBeta.cs.getsockname(), beta.connector.cs.getpeername())
        self.assertEqual(ixBeta.cs.getpeername(), beta.connector.cs.getsockname())
        self.assertEqual(ixBeta.ca, beta.connector.ca)
        self.assertEqual(ixBeta.ha, beta.connector.ha)

        beta.transmit()

        lines = [
                   b'GET /echo?name=fame HTTP/1.1',
                   b'Host: 127.0.0.1:6101',
                   b'Accept-Encoding: identity',
                   b'Content-Length: 0',
                   b'Accept: application/json',
                   b'',
                   b'',
                ]
        for i, line in enumerate(lines):
            self.assertEqual(line, beta.requester.lines[i])

        msgOut = beta.connector.txes[0]
        self.assertEqual(beta.requester.head, b'GET /echo?name=fame HTTP/1.1\r\nHost: 127.0.0.1:6101\r\nAccept-Encoding: identity\r\nContent-Length: 0\r\nAccept: application/json\r\n\r\n')
        self.assertEqual(msgOut, b'GET /echo?name=fame HTTP/1.1\r\nHost: 127.0.0.1:6101\r\nAccept-Encoding: identity\r\nContent-Length: 0\r\nAccept: application/json\r\n\r\n')

        console.terse("Beta requests to Alpha\n")
        console.terse("{0} from  {1}:{2}{3} ...\n".format(method, host, port, path))

        while beta.connector.txes and not ixBeta.rxbs :
            beta.serviceAll()
            time.sleep(0.05)
            alpha.serviceAllRxAllIx()
            time.sleep(0.05)
        msgIn = bytes(ixBeta.rxbs)
        self.assertEqual(msgIn, msgOut)
        ixBeta.clearRxbs()

        console.terse("Alpha responds to Beta\n")
        console.terse("Beta processes response \n")
        msgOut = b'HTTP/1.1 200 OK\r\nContent-Length: 122\r\nContent-Type: application/json\r\nDate: Thu, 30 Apr 2015 19:37:17 GMT\r\nServer: IoBook.local\r\n\r\n{"content": null, "query": {"name": "fame"}, "verb": "GET", "url": "http://127.0.0.1:8080/echo?name=fame", "action": null}'
        ixBeta.tx(msgOut)
        while ixBeta.txes or not beta.respondent.ended:
            alpha.serviceTxesAllIx()
            time.sleep(0.05)
            beta.serviceAll()
            time.sleep(0.05)

        self.assertEqual(len(beta.connector.rxbs), 0)
        self.assertIs(beta.waited, False)
        self.assertIs(beta.respondent.ended, True)
        self.assertEqual(len(beta.responses), 1)

        self.assertEqual(bytes(beta.respondent.body), b'{"content": null, "query": {"name": "fame"}, "verb": "GET", "url": "http://127.0.0.1:8080/echo?name=fame", "action": null}')
        self.assertEqual(len(beta.connector.rxbs), 0)
        self.assertEqual(beta.respondent.headers.items(), [('content-length', '122'),
                                                    ('content-type', 'application/json'),
                                                    ('date', 'Thu, 30 Apr 2015 19:37:17 GMT'),
                                                    ('server', 'IoBook.local')])

        alpha.close()
        beta.connector.close()

        wireLogAlpha.close()
        wireLogBeta.close()
        console.reinit(verbosity=console.Wordage.concise)


    def testPatronPipelineEcho(self):
        """
        Test Patron pipeline servicing
        """
        console.terse("{0}\n".format(self.testPatronPipelineEcho.__doc__))

        console.reinit(verbosity=console.Wordage.profuse)

        wireLogAlpha = nonblocking.WireLog(buffify=True, same=True)
        result = wireLogAlpha.reopen()

        alpha = nonblocking.Server(port = 6101, bufsize=131072, wlog=wireLogAlpha)
        self.assertIs(alpha.reopen(), True)
        self.assertEqual(alpha.ha, ('0.0.0.0', 6101))
        self.assertEqual(alpha.eha, ('127.0.0.1', 6101))

        console.terse("{0}\n".format("Building Connector ...\n"))

        wireLogBeta = nonblocking.WireLog(buffify=True,  same=True)
        result = wireLogBeta.reopen()
        host = alpha.eha[0]
        port = alpha.eha[1]

        beta = httping.Patron(bufsize=131072,
                                     wlog=wireLogBeta,
                                     host=host,
                                     port=port,
                                     reconnectable=True,
                                     )

        self.assertIs(beta.connector.reopen(), True)
        self.assertIs(beta.connector.accepted, False)
        self.assertIs(beta.connector.connected, False)
        self.assertIs(beta.connector.cutoff, False)

        console.terse("Connecting beta to server ...\n")
        while True:
            beta.connector.serviceConnect()
            alpha.serviceConnects()
            if beta.connector.connected and beta.connector.ca in alpha.ixes:
                break
            time.sleep(0.05)

        self.assertIs(beta.connector.accepted, True)
        self.assertIs(beta.connector.connected, True)
        self.assertIs(beta.connector.cutoff, False)
        self.assertEqual(beta.connector.ca, beta.connector.cs.getsockname())
        self.assertEqual(beta.connector.ha, beta.connector.cs.getpeername())
        self.assertEqual(alpha.eha, beta.connector.ha)

        ixBeta = alpha.ixes[beta.connector.ca]
        self.assertIsNotNone(ixBeta.ca)
        self.assertIsNotNone(ixBeta.cs)
        self.assertEqual(ixBeta.cs.getsockname(), beta.connector.cs.getpeername())
        self.assertEqual(ixBeta.cs.getpeername(), beta.connector.cs.getsockname())
        self.assertEqual(ixBeta.ca, beta.connector.ca)
        self.assertEqual(ixBeta.ha, beta.connector.ha)

        request = odict([('method', u'GET'),
                         ('path', u'/echo?name=fame'),
                         ('qargs', odict()),
                         ('fragment', u''),
                         ('headers', odict([('Accept', 'application/json')])),
                         ('body', None),
                        ])

        beta.requests.append(request)

        console.terse("Beta requests to Alpha\n")
        console.terse("from {0}:{1}, {2} {3} ...\n".format(beta.connector.ha[0],
                                                         beta.connector.ha[1],
                                                         request['method'],
                                                         request['path']))

        while (beta.requests or beta.connector.txes) and not ixBeta.rxbs :
            beta.serviceAll()
            time.sleep(0.05)
            alpha.serviceAllRxAllIx()
            time.sleep(0.05)
        msgIn = bytes(ixBeta.rxbs)
        msgOut = b'GET /echo?name=fame HTTP/1.1\r\nHost: 127.0.0.1:6101\r\nAccept-Encoding: identity\r\nContent-Length: 0\r\nAccept: application/json\r\n\r\n'
        self.assertEqual(msgIn, msgOut)
        ixBeta.clearRxbs()

        console.terse("Alpha responds to Beta\n")
        console.terse("Beta processes response \n")
        msgOut = b'HTTP/1.1 200 OK\r\nContent-Length: 122\r\nContent-Type: application/json\r\nDate: Thu, 30 Apr 2015 19:37:17 GMT\r\nServer: IoBook.local\r\n\r\n{"content": null, "query": {"name": "fame"}, "verb": "GET", "url": "http://127.0.0.1:8080/echo?name=fame", "action": null}'
        ixBeta.tx(msgOut)
        while ixBeta.txes or not beta.respondent.ended:
            alpha.serviceTxesAllIx()
            time.sleep(0.05)
            beta.serviceAll()
            time.sleep(0.05)

        self.assertEqual(len(beta.connector.rxbs), 0)
        self.assertIs(beta.waited, False)
        self.assertIs(beta.respondent.ended, True)

        self.assertEqual(len(beta.responses), 1)
        response = beta.responses.popleft()
        self.assertEqual(response, {'version': 11,
                                    'status': 200,
                                    'reason': 'OK',
                                    'headers':
                                        {'content-length': '122',
                                        'content-type': 'application/json',
                                        'date': 'Thu, 30 Apr 2015 19:37:17 GMT',
                                        'server': 'IoBook.local'},
                                    'body': bytearray(b'{"content": null, "query": {"name": "fame"}, "verb": "GET", "url": "http://127.0.0.1:8080/echo?name=fame", "action": null}'),
                                    'data': None,
                                    'request':
                                        {'host': '127.0.0.1',
                                         'port': 6101,
                                         'scheme': 'http',
                                         'method': 'GET',
                                         'path': '/echo',
                                         'qargs': {'name': 'fame'},
                                         'fragment': '',
                                         'headers':
                                             {'Accept': 'application/json'},
                                         'body': b''
                                        }
                                    })

        beta.requests.append(request)

        console.terse("\nBeta requests to Alpha again\n")
        console.terse("from {0}:{1}, {2} {3} ...\n".format(beta.connector.ha[0],
                                                           beta.connector.ha[1],
                                                           request['method'],
                                                           request['path']))

        while (beta.requests or beta.connector.txes) and not ixBeta.rxbs :
            beta.serviceAll()
            time.sleep(0.05)
            alpha.serviceAllRxAllIx()
            time.sleep(0.05)
        msgIn = bytes(ixBeta.rxbs)
        msgOut = b'GET /echo?name=fame HTTP/1.1\r\nHost: 127.0.0.1:6101\r\nAccept-Encoding: identity\r\nContent-Length: 0\r\nAccept: application/json\r\n\r\n'
        self.assertEqual(msgIn, msgOut)
        ixBeta.clearRxbs()

        console.terse("Alpha responds to Beta\n")
        console.terse("Beta processes response \n")
        msgOut = b'HTTP/1.1 200 OK\r\nContent-Length: 122\r\nContent-Type: application/json\r\nDate: Thu, 30 Apr 2015 19:37:17 GMT\r\nServer: IoBook.local\r\n\r\n{"content": null, "query": {"name": "fame"}, "verb": "GET", "url": "http://127.0.0.1:8080/echo?name=fame", "action": null}'
        ixBeta.tx(msgOut)
        while ixBeta.txes or not beta.respondent.ended:
            alpha.serviceTxesAllIx()
            time.sleep(0.05)
            beta.serviceAll()
            time.sleep(0.05)

        self.assertEqual(len(beta.connector.rxbs), 0)
        self.assertIs(beta.waited, False)
        self.assertIs(beta.respondent.ended, True)

        self.assertEqual(len(beta.responses), 1)
        response = beta.responses.popleft()
        self.assertEqual(response, {'version': 11,
                                    'status': 200,
                                    'reason': 'OK',
                                    'headers':
                                        {'content-length': '122',
                                         'content-type': 'application/json',
                                         'date': 'Thu, 30 Apr 2015 19:37:17 GMT',
                                         'server': 'IoBook.local'},
                                    'body': bytearray(b'{"content": null, "query": {"name": "fame"}, "verb": "GET", "url": "http://127.0.0.1:8080/echo?name=fame", "action": null}'),
                                    'data': None,
                                    'request': {'host': '127.0.0.1',
                                                'port': 6101,
                                                'scheme': 'http',
                                                'method': 'GET',
                                                'path': '/echo',
                                                'qargs': {'name': 'fame'},
                                                'fragment': '',
                                                'headers': {'Accept': 'application/json'},
                                                'body': b''}
                                    })

        alpha.close()
        beta.connector.close()

        wireLogAlpha.close()
        wireLogBeta.close()
        console.reinit(verbosity=console.Wordage.concise)

    def mockEchoService(self, server):
        """
        mock echo server service
        """
        server.serviceConnects()
        if server.ixes:
            server.serviceAllRxAllIx()

            ixClient = server.ixes.values()[0]
            msgIn = bytes(ixClient.rxbs)
            if  msgIn== b'GET /echo?name=fame HTTP/1.1\r\nHost: 127.0.0.1:6101\r\nAccept-Encoding: identity\r\nContent-Length: 0\r\nAccept: application/json\r\n\r\n':
                ixClient.clearRxbs()
                msgOut = b'HTTP/1.1 200 OK\r\nContent-Length: 122\r\nContent-Type: application/json\r\nDate: Thu, 30 Apr 2015 19:37:17 GMT\r\nServer: IoBook.local\r\n\r\n{"content": null, "query": {"name": "fame"}, "verb": "GET", "url": "http://127.0.0.1:8080/echo?name=fame", "action": null}'
                ixClient.tx(msgOut)
                msgIn = b''
                msgOut = b''

            server.serviceTxesAllIx()

    def testPatronPipelineEchoSimple(self):
        """
        Test Patron pipeline servicing
        """
        console.terse("{0}\n".format(self.testPatronPipelineEchoSimple.__doc__))

        console.reinit(verbosity=console.Wordage.profuse)

        wireLogAlpha = nonblocking.WireLog(buffify=True, same=True)
        result = wireLogAlpha.reopen()

        alpha = nonblocking.Server(port = 6101, bufsize=131072, wlog=wireLogAlpha)
        self.assertIs(alpha.reopen(), True)
        self.assertEqual(alpha.ha, ('0.0.0.0', 6101))
        self.assertEqual(alpha.eha, ('127.0.0.1', 6101))

        console.terse("{0}\n".format("Building Connector ...\n"))

        wireLogBeta = nonblocking.WireLog(buffify=True,  same=True)
        result = wireLogBeta.reopen()
        host = alpha.eha[0]
        port = alpha.eha[1]

        beta = httping.Patron(bufsize=131072,
                                     wlog=wireLogBeta,
                                     host=host,
                                     port=port,
                                     reconnectable=True,
                                     )

        self.assertIs(beta.connector.reopen(), True)
        self.assertIs(beta.connector.accepted, False)
        self.assertIs(beta.connector.connected, False)
        self.assertIs(beta.connector.cutoff, False)

        request = odict([('method', u'GET'),
                         ('path', u'/echo?name=fame'),
                         ('qargs', odict()),
                         ('fragment', u''),
                         ('headers', odict([('Accept', 'application/json')])),
                         ('body', None),
                        ])

        beta.requests.append(request)

        while not alpha.ixes or beta.requests or beta.connector.txes or not beta.respondent.ended:
            self.mockEchoService(alpha)
            time.sleep(0.05)
            beta.serviceAll()
            time.sleep(0.05)

        self.assertEqual(len(beta.connector.rxbs), 0)
        self.assertIs(beta.waited, False)
        self.assertIs(beta.respondent.ended, True)

        self.assertEqual(len(beta.responses), 1)
        response = beta.responses.popleft()
        self.assertEqual(response, {'version': 11,
                                    'status': 200,
                                    'reason': 'OK',
                                    'headers':
                                        {'content-length': '122',
                                        'content-type': 'application/json',
                                        'date': 'Thu, 30 Apr 2015 19:37:17 GMT',
                                        'server': 'IoBook.local'},
                                    'body': bytearray(b'{"content": null, "query": {"name": "fame"}, "verb": "GET", "url": "http://127.0.0.1:8080/echo?name=fame", "action": null}'),
                                    'data': None,
                                    'request':
                                        {'host': '127.0.0.1',
                                         'port': 6101,
                                         'scheme': 'http',
                                         'method': 'GET',
                                         'path': '/echo',
                                         'qargs': {'name': 'fame'},
                                         'fragment': '',
                                         'headers':
                                             {'Accept': 'application/json'},
                                         'body': b''
                                        }
                                    })

        beta.requests.append(request)

        while not alpha.ixes or beta.requests or beta.connector.txes or not beta.respondent.ended:
            self.mockEchoService(alpha)
            time.sleep(0.05)
            beta.serviceAll()
            time.sleep(0.05)

        self.assertEqual(len(beta.connector.rxbs), 0)
        self.assertIs(beta.waited, False)
        self.assertIs(beta.respondent.ended, True)

        self.assertEqual(len(beta.responses), 1)
        response = beta.responses.popleft()
        self.assertEqual(response, {'version': 11,
                                    'status': 200,
                                    'reason': 'OK',
                                    'headers':
                                        {'content-length': '122',
                                        'content-type': 'application/json',
                                        'date': 'Thu, 30 Apr 2015 19:37:17 GMT',
                                        'server': 'IoBook.local'},
                                    'body': bytearray(b'{"content": null, "query": {"name": "fame"}, "verb": "GET", "url": "http://127.0.0.1:8080/echo?name=fame", "action": null}'),
                                    'data': None,
                                    'request':
                                        {'host': '127.0.0.1',
                                         'port': 6101,
                                         'scheme': 'http',
                                         'method': 'GET',
                                         'path': '/echo',
                                         'qargs': {'name': 'fame'},
                                         'fragment': '',
                                         'headers':
                                             {'Accept': 'application/json'},
                                         'body': b''
                                        }
                                    })

        alpha.close()
        beta.connector.close()

        wireLogAlpha.close()
        wireLogBeta.close()
        console.reinit(verbosity=console.Wordage.concise)


    def testPatronPipelineStream(self):
        """
        Test Patron pipeline stream
        """
        console.terse("{0}\n".format(self.testPatronPipelineStream.__doc__))

        console.reinit(verbosity=console.Wordage.profuse)

        wireLogAlpha = nonblocking.WireLog(buffify=True, same=True)
        result = wireLogAlpha.reopen()

        alpha = nonblocking.Server(port = 6101, bufsize=131072, wlog=wireLogAlpha)
        self.assertIs(alpha.reopen(), True)
        self.assertEqual(alpha.ha, ('0.0.0.0', 6101))
        self.assertEqual(alpha.eha, ('127.0.0.1', 6101))

        console.terse("{0}\n".format("Building Connector ...\n"))

        wireLogBeta = nonblocking.WireLog(buffify=True,  same=True)
        result = wireLogBeta.reopen()
        host = alpha.eha[0]
        port = alpha.eha[1]

        store = storing.Store(stamp=0.0)

        beta = httping.Patron(bufsize=131072,
                                 wlog=wireLogBeta,
                                 host=host,
                                 port=port,
                                 store=store,
                                 reconnectable=True,
                                 )

        self.assertIs(beta.connector.reopen(), True)
        self.assertIs(beta.connector.accepted, False)
        self.assertIs(beta.connector.connected, False)
        self.assertIs(beta.connector.cutoff, False)

        console.terse("Connecting beta to server ...\n")
        while True:
            beta.serviceAll()
            alpha.serviceConnects()
            if beta.connector.connected and beta.connector.ca in alpha.ixes:
                break
            time.sleep(0.05)
            beta.connector.store.advanceStamp(0.05)

        self.assertIs(beta.connector.accepted, True)
        self.assertIs(beta.connector.connected, True)
        self.assertIs(beta.connector.cutoff, False)
        self.assertEqual(beta.connector.ca, beta.connector.cs.getsockname())
        self.assertEqual(beta.connector.ha, beta.connector.cs.getpeername())
        self.assertEqual(alpha.eha, beta.connector.ha)

        ixBeta = alpha.ixes[beta.connector.ca]
        self.assertIsNotNone(ixBeta.ca)
        self.assertIsNotNone(ixBeta.cs)
        self.assertEqual(ixBeta.cs.getsockname(), beta.connector.cs.getpeername())
        self.assertEqual(ixBeta.cs.getpeername(), beta.connector.cs.getsockname())
        self.assertEqual(ixBeta.ca, beta.connector.ca)
        self.assertEqual(ixBeta.ha, beta.connector.ha)

        console.terse("{0}\n".format("Building Request ...\n"))
        request = odict([('method', u'GET'),
                         ('path', u'/stream'),
                         ('qargs', odict()),
                         ('fragment', u''),
                         ('headers', odict([('Accept', 'application/json')])),
                         ('body', None),
                        ])

        beta.requests.append(request)

        console.terse("Beta requests to Alpha\n")
        console.terse("from {0}:{1}, {2} {3} ...\n".format(beta.connector.ha[0],
                                                         beta.connector.ha[1],
                                                         request['method'],
                                                         request['path']))

        while (beta.requests or beta.connector.txes) and not ixBeta.rxbs :
            beta.serviceAll()
            time.sleep(0.05)
            beta.connector.store.advanceStamp(0.05)
            alpha.serviceAllRxAllIx()
            time.sleep(0.05)
            beta.connector.store.advanceStamp(0.05)

        msgIn = bytes(ixBeta.rxbs)
        msgOut = b'GET /stream HTTP/1.1\r\nHost: 127.0.0.1:6101\r\nAccept-Encoding: identity\r\nContent-Length: 0\r\nAccept: application/json\r\n\r\n'

        self.assertEqual(msgIn, msgOut)
        ixBeta.clearRxbs()

        console.terse("Alpha responds to Beta\n")
        lines = [
            b'HTTP/1.0 200 OK\r\n',
            b'Server: PasteWSGIServer/0.5 Python/2.7.9\r\n',
            b'Date: Thu, 30 Apr 2015 21:35:25 GMT\r\n'
            b'Content-Type: text/event-stream\r\n',
            b'Cache-Control: no-cache\r\n',
            b'Connection: close\r\n\r\n',
            b'retry: 1000\n\n',
            b'id: 0\ndata: START\n\n',
            b'id: 1\ndata: 1\ndata: 2\n\n',
            b'id: 2\ndata: 3\ndata: 4\n\n',
            b'id: 3\ndata: 5\ndata: 6\n\n',
            b'id: 4\ndata: 7\ndata: 8\n\n',
        ]

        msgOut = b''.join(lines)
        ixBeta.tx(msgOut)
        timer = StoreTimer(store=store, duration=0.5)
        while ixBeta.txes or not timer.expired:
            alpha.serviceTxesAllIx()
            time.sleep(0.05)
            beta.connector.store.advanceStamp(0.05)
            beta.serviceAll()
            time.sleep(0.05)
            beta.connector.store.advanceStamp(0.05)

        self.assertEqual(len(beta.connector.rxbs), 0)

        #timed out while stream still open so no responses in .responses
        self.assertIs(beta.waited, True)
        self.assertIs(beta.respondent.ended, False)
        self.assertEqual(len(beta.responses), 0)

        # but are events in .events
        self.assertEqual(len(beta.events), 5)
        self.assertEqual(beta.respondent.retry, 1000)
        self.assertEqual(beta.respondent.leid, '4')
        event = beta.events.popleft()
        self.assertEqual(event, {'id': '0', 'name': '', 'data': 'START', 'json': None})
        event = beta.events.popleft()
        self.assertEqual(event, {'id': '1', 'name': '', 'data': '1\n2', 'json': None})
        event = beta.events.popleft()
        self.assertEqual(event, {'id': '2', 'name': '', 'data': '3\n4', 'json': None})
        beta.events.clear()

        # alpha's ixBeta connection shutdown prematurely
        console.terse("Disconnecting server so beta must auto reconnect ...\n")
        alpha.shutcloseIx(beta.connector.ca)
        alpha.removeIx(beta.connector.ca)
        while True:
            beta.serviceAll()
            if not beta.connector.connected:
                break
            time.sleep(0.1)
            beta.connector.store.advanceStamp(0.1)

        self.assertIs(beta.connector.cutoff, False)

        console.terse("Auto reconnecting beta and rerequesting...\n")
        while True:
            beta.serviceAll()
            alpha.serviceConnects()
            if beta.connector.connected and beta.connector.ca in alpha.ixes:
                break
            time.sleep(0.05)
            beta.connector.store.advanceStamp(0.05)

        self.assertIs(beta.connector.accepted, True)
        self.assertIs(beta.connector.connected, True)
        self.assertIs(beta.connector.cutoff, False)
        self.assertEqual(beta.connector.ca, beta.connector.cs.getsockname())
        self.assertEqual(beta.connector.ha, beta.connector.cs.getpeername())
        self.assertEqual(alpha.eha, beta.connector.ha)

        ixBeta = alpha.ixes[beta.connector.ca]
        self.assertIsNotNone(ixBeta.ca)
        self.assertIsNotNone(ixBeta.cs)
        self.assertEqual(ixBeta.cs.getsockname(), beta.connector.cs.getpeername())
        self.assertEqual(ixBeta.cs.getpeername(), beta.connector.cs.getsockname())
        self.assertEqual(ixBeta.ca, beta.connector.ca)
        self.assertEqual(ixBeta.ha, beta.connector.ha)

        console.terse("Server receiving...\n")
        while (beta.requests or beta.connector.txes) or not ixBeta.rxbs:
            beta.serviceAll()
            time.sleep(0.05)
            beta.connector.store.advanceStamp(0.05)
            alpha.serviceAllRxAllIx()
            time.sleep(0.05)
            beta.connector.store.advanceStamp(0.05)

        msgIn = bytes(ixBeta.rxbs)
        msgOut = b'GET /stream HTTP/1.1\r\nHost: 127.0.0.1:6101\r\nAccept-Encoding: identity\r\nContent-Length: 0\r\nAccept: application/json\r\nLast-Event-Id: 4\r\n\r\n'

        self.assertEqual(msgIn, msgOut)
        ixBeta.clearRxbs()

        console.terse("Alpha responds to Beta\n")
        lines = [
            b'HTTP/1.0 200 OK\r\n',
            b'Server: PasteWSGIServer/0.5 Python/2.7.9\r\n',
            b'Date: Thu, 30 Apr 2015 21:35:25 GMT\r\n'
            b'Content-Type: text/event-stream\r\n',
            b'Cache-Control: no-cache\r\n',
            b'Connection: close\r\n\r\n',
            b'id: 5\ndata: 9\ndata: 10\n\n',
            b'id: 6\ndata: 11\ndata: 12\n\n',
        ]

        msgOut = b''.join(lines)
        ixBeta.tx(msgOut)
        timer = StoreTimer(store=store, duration=0.5)
        while ixBeta.txes or not timer.expired:
            alpha.serviceTxesAllIx()
            time.sleep(0.05)
            beta.connector.store.advanceStamp(0.05)
            beta.serviceAll()
            time.sleep(0.05)
            beta.connector.store.advanceStamp(0.05)

        self.assertEqual(len(beta.connector.rxbs), 0)

        #timed out while stream still open so no responses in .responses
        self.assertIs(beta.waited, True)
        self.assertIs(beta.respondent.ended, False)
        self.assertEqual(len(beta.responses), 0)

        # but are events in .events
        self.assertEqual(len(beta.events), 2)
        self.assertEqual(beta.respondent.retry, 1000)
        self.assertEqual(beta.respondent.leid, '6')
        event = beta.events.popleft()
        self.assertEqual(event, {'id': '5', 'name': '', 'data': '9\n10', 'json': None})
        event = beta.events.popleft()
        self.assertEqual(event, {'id': '6', 'name': '', 'data': '11\n12', 'json': None})


        alpha.close()
        beta.connector.close()

        wireLogAlpha.close()
        wireLogBeta.close()
        console.reinit(verbosity=console.Wordage.concise)

    def mockEchoServiceSecure(self, server):
        """
        mock echo server service TLS secure
        """
        server.serviceConnects()
        if server.ixes:
            server.serviceAllRxAllIx()

            ixClient = server.ixes.values()[0]
            msgIn = bytes(ixClient.rxbs)
            if  msgIn== b'GET /echo?name=fame HTTP/1.1\r\nHost: localhost:6101\r\nAccept-Encoding: identity\r\nContent-Length: 0\r\nAccept: application/json\r\n\r\n':
                ixClient.clearRxbs()
                msgOut = b'HTTP/1.1 200 OK\r\nContent-Length: 122\r\nContent-Type: application/json\r\nDate: Thu, 30 Apr 2015 19:37:17 GMT\r\nServer: IoBook.local\r\n\r\n{"content": null, "query": {"name": "fame"}, "verb": "GET", "url": "http://127.0.0.1:8080/echo?name=fame", "action": null}'
                ixClient.tx(msgOut)
                msgIn = b''
                msgOut = b''

            server.serviceTxesAllIx()

    def testPatronPipelineEchoSimpleSecure(self):
        """
        Test Patron pipeline servicing
        """
        console.terse("{0}\n".format(self.testPatronPipelineEchoSimpleSecure.__doc__))

        console.reinit(verbosity=console.Wordage.profuse)

        wireLogAlpha = nonblocking.WireLog(buffify=True, same=True)
        result = wireLogAlpha.reopen()

        serverKeypath = '/etc/pki/tls/certs/server_key.pem'  # local server private key
        serverCertpath = '/etc/pki/tls/certs/server_cert.pem'  # local server public cert
        clientCafilepath = '/etc/pki/tls/certs/client.pem' # remote client public cert

        clientKeypath = '/etc/pki/tls/certs/client_key.pem'  # local client private key
        clientCertpath = '/etc/pki/tls/certs/client_cert.pem'  # local client public cert
        serverCafilepath = '/etc/pki/tls/certs/server.pem' # remote server public cert

        serverCertCommonName = 'localhost' # match hostname uses servers's cert commonname

        alpha = nonblocking.ServerTls(host=serverCertCommonName,
                                      port = 6101,
                                      bufsize=131072,
                                      wlog=wireLogAlpha,
                                      context=None,
                                      version=None,
                                      certify=None,
                                      keypath=serverKeypath,
                                      certpath=serverCertpath,
                                      cafilepath=clientCafilepath,
                                      )
        self.assertIs(alpha.reopen(), True)
        self.assertEqual(alpha.ha, ('127.0.0.1', 6101))
        self.assertEqual(alpha.eha, ('127.0.0.1', 6101))

        console.terse("{0}\n".format("Building Patron ...\n"))

        wireLogBeta = nonblocking.WireLog(buffify=True,  same=True)
        result = wireLogBeta.reopen()
        host = alpha.eha[0]
        port = alpha.eha[1]

        beta = httping.Patron(host=serverCertCommonName,
                              port=alpha.eha[1],
                              bufsize=131072,
                              wlog=wireLogBeta,
                              scheme='https',
                              reconnectable=True,
                              certedhost=serverCertCommonName,
                              keypath=clientKeypath,
                              certpath=clientCertpath,
                              cafilepath=serverCafilepath,
                            )

        self.assertIs(beta.connector.reopen(), True)
        self.assertIs(beta.connector.accepted, False)
        self.assertIs(beta.connector.connected, False)
        self.assertIs(beta.connector.cutoff, False)

        request = odict([('method', u'GET'),
                         ('path', u'/echo?name=fame'),
                         ('qargs', odict()),
                         ('fragment', u''),
                         ('headers', odict([('Accept', 'application/json')])),
                         ('body', None),
                        ])

        beta.requests.append(request)

        while not alpha.ixes or beta.requests or beta.connector.txes or not beta.respondent.ended:
            self.mockEchoServiceSecure(alpha)
            time.sleep(0.05)
            beta.serviceAll()
            time.sleep(0.05)

        self.assertEqual(len(beta.connector.rxbs), 0)
        self.assertIs(beta.waited, False)
        self.assertIs(beta.respondent.ended, True)

        self.assertEqual(len(beta.responses), 1)
        response = beta.responses.popleft()
        self.assertEqual(response, {'version': 11,
                                    'status': 200,
                                    'reason': 'OK',
                                    'headers':
                                        {'content-length': '122',
                                        'content-type': 'application/json',
                                        'date': 'Thu, 30 Apr 2015 19:37:17 GMT',
                                        'server': 'IoBook.local'},
                                    'body': bytearray(b'{"content": null, "query": {"name": "fame"}, "verb": "GET", "url": "http://127.0.0.1:8080/echo?name=fame", "action": null}'),
                                    'data': None,
                                    'request':
                                        {'host': 'localhost',
                                         'port': 6101,
                                         'scheme': 'https',
                                         'method': 'GET',
                                         'path': '/echo',
                                         'qargs': {'name': 'fame'},
                                         'fragment': '',
                                         'headers':
                                             {'Accept': 'application/json'},
                                         'body': b''
                                        }
                                    })

        beta.requests.append(request)

        while not alpha.ixes or beta.requests or beta.connector.txes or not beta.respondent.ended:
            self.mockEchoServiceSecure(alpha)
            time.sleep(0.05)
            beta.serviceAll()
            time.sleep(0.05)

        self.assertEqual(len(beta.connector.rxbs), 0)
        self.assertIs(beta.waited, False)
        self.assertIs(beta.respondent.ended, True)

        self.assertEqual(len(beta.responses), 1)
        response = beta.responses.popleft()
        self.assertEqual(response, {'version': 11,
                                    'status': 200,
                                    'reason': 'OK',
                                    'headers':
                                        {'content-length': '122',
                                        'content-type': 'application/json',
                                        'date': 'Thu, 30 Apr 2015 19:37:17 GMT',
                                        'server': 'IoBook.local'},
                                    'body': bytearray(b'{"content": null, "query": {"name": "fame"}, "verb": "GET", "url": "http://127.0.0.1:8080/echo?name=fame", "action": null}'),
                                    'data': None,
                                    'request':
                                        {'host': 'localhost',
                                         'port': 6101,
                                         'scheme': 'https',
                                         'method': 'GET',
                                         'path': '/echo',
                                         'qargs': {'name': 'fame'},
                                         'fragment': '',
                                         'headers':
                                             {'Accept': 'application/json'},
                                         'body': b''
                                        }
                                    })

        alpha.close()
        beta.connector.close()

        wireLogAlpha.close()
        wireLogBeta.close()
        console.reinit(verbosity=console.Wordage.concise)



def runOne(test):
    '''
    Unittest Runner
    '''
    test = BasicTestCase(test)
    suite = unittest.TestSuite([test])
    unittest.TextTestRunner(verbosity=2).run(suite)

def runSome():
    """ Unittest runner """
    tests =  []
    names = [
             'testNonBlockingRequestEcho',
             'testNonBlockingRequestStream',
             'testNonBlockingRequestStreamChunked',
             'testNonBlockingRequestStreamFancy',
             'testNonBlockingRequestStreamFancyChunked',
             'testNonBlockingRequestStreamFancyJson',
             'testNonBlockingRequestStreamFancyJsonChunked',
             'testNonBlockingRequestEchoTLS',
             'testPatronRequestEcho',
             'testPatronServiceEcho',
             'testPatronPipelineEcho',
             'testPatronPipelineEchoSimple',
             'testPatronPipelineStream',
             'testPatronPipelineEchoSimpleSecure',
            ]
    tests.extend(map(BasicTestCase, names))
    suite = unittest.TestSuite(tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

def runAll():
    """ Unittest runner """
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(BasicTestCase))
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__' and __package__ is None:

    #console.reinit(verbosity=console.Wordage.concise)

    #runAll() #run all unittests

    runSome()#only run some

    #runOne('testPatronRequestEcho')
    #runOne('testPatronServiceEcho')
    #runOne('testPatronPipelineEcho')
    #runOne('testPatronPipelineStream')
    #runOne('testPatronPipelineEchoSimpleSecure')
    #runOne('testPatronSecurePipelineEcho')
