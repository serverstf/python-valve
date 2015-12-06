import functools
import copy

import six.moves.socketserver as socketserver

import valve.source.rcon


class ExpectedRCONMessage(valve.source.rcon.RCONMessage):

    def __init__(self, id_, type_, body):
        valve.source.rcon.RCONMessage.__init__(self, id_, type_, body)
        self.responses = []

    def respond(self, id_, type_, body):
        response = functools.partial(
            TestRCONHandler.send_message,
            message=valve.source.rcon.RCONMessage(id_, type_, body),
        )
        self.responses.append(response)

    def respond_close(self):
        self.responses.append(TestRCONHandler.close)

    def respond_terminate_multi_part(self, id_):
        self.respond(
            id_, valve.source.rcon.RCONMessage.Type.RESPONSE_VALUE, b"")
        self.respond(
            id_,
            valve.source.rcon.RCONMessage.Type.RESPONSE_VALUE,
            b"\x00\x01\x00\x00",
        )


class TestRCONHandler(socketserver.BaseRequestHandler):

    def _decode_messages(self, buffer_):
        while buffer_:
            try:
                message, buffer_ = \
                    valve.source.rcon.RCONMessage.decode(buffer_)
            except valve.source.rcon.RCONMessageError:
                return
            else:
                yield message

    def _handle_request(self, message):
        if not self._expectations:
            raise Exception("Unexpected message {}".format(message))
        expected = self._expectations.pop(0)
        for attribute in ['id', 'type', 'body']:
            a_message = getattr(message, attribute)
            a_expected = getattr(expected, attribute)
            if a_message != a_expected:
                raise Exception("Expected {} == {!r}, got {!r}".format(
                    attribute, a_expected, a_message))
        for response in expected.responses:
            response(self)

    def send_message(self, message):
        self.request.sendall(message.encode())

    def close(self):
        self.request.close()

    def setup(self):
        self._expectations = self.server.expectations()

    def handle(self):
        buffer_ = b""
        while True:
            received = self.request.recv(4096)
            if not received:
                return
            buffer_ += received
            for message in self._decode_messages(buffer_):
                self._handle_request(message)


class TestRCONServer(socketserver.TCPServer):

    def __init__(self):
        socketserver.TCPServer.__init__(self, ('', 0), TestRCONHandler)
        self._expectations = []

    def expect(self, id_, type_, body):
        self._expectations.append(ExpectedRCONMessage(id_, type_, body))
        return self._expectations[-1]

    def expectations(self):
        return copy.deepcopy(self._expectations)
