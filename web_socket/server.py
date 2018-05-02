import logging.config

from autobahn.twisted.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory
from twisted.protocols import basic


logging.config.fileConfig("config/logging_config.ini")
logger = logging.getLogger(__name__)


class UserInputProtocol(basic.LineReceiver):
    from os import linesep as delimiter

    delimiter = delimiter.encode("utf8")

    def __init__(self, callback):
        self.callback = callback

    def lineReceived(self, line):
        self.callback(line)


class MyServerProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        logger.debug("Client connecting: {0}".format(request.peer))
        self.factory.protocol_pool.append(self)

    def onOpen(self):
        logger.debug("WebSocket connection open.")

    def onMessage(self, payload, isBinary):
        if isBinary:
            logger.debug("Binary message received: {0} bytes".format(len(payload)))
        else:
            logger.debug("Text message received: {0}".format(payload.decode("utf8")))

        # echo back message verbatim
        self.sendMessage(payload, isBinary)

    def onClose(self, wasClean, code, reason):
        logger.debug("WebSocket connection closed: {0}".format(reason))
        self.factory.protocol_pool.remove(self)

    def send_package(self, data, sender="client", vin="haha", package_type="unknown"):
        from utils.deconstruct_package import deconstruct_hex_package
        dic = deconstruct_hex_package(data)

        dic["sender"] = sender
        dic["package_type"] = package_type
        import datetime
        dic["datetime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        dic["vin"] = vin

        # truncat payload by length
        length = int(dic["length"], 16)
        logger.debug(length)
        logger.debug(dic["payload"])
        if len(dic["payload"]) > 2 * length:
            dic["checksum"] = dic["payload"][2 * length:2 * length + 2]
            dic["payload"] = dic["payload"][:2 * length]

        import json
        logger.debug(dic)
        data = json.dumps(dic).encode("ascii")
        logger.debug(data)

        self.sendMessage(data, False)


class DebugPackageServerFactory(WebSocketServerFactory):

    protocol = MyServerProtocol

    def __init__(self):
        from twisted.internet import stdio
        stdio.StandardIO(UserInputProtocol(self.user_input_received))

        super(DebugPackageServerFactory, self).__init__(
            "ws://127.0.0.1:{port}".format(port=9000)
        )
        self.protocol_pool = []

    def user_input_received(self, data):
        """
        Process user input

        :param data:
        :type data: bytes
        """
        import binascii
        hex_representation = binascii.hexlify(data).decode("ascii")
        logger.debug(hex_representation)
        import re
        match = re.search(r"2323\w+", hex_representation)
        if match:
            package = match.group(0)[:-12]
            logger.debug(package)
            if len(package) > 10:
                self.broadcast_packages(package)

    def broadcast_packages(self, data):
        for protocol in self.protocol_pool:
            protocol.send_package(data)


def main():
    import sys

    from twisted.internet import reactor

    factory = DebugPackageServerFactory()
    factory.protocol = MyServerProtocol

    reactor.listenTCP(9000, factory)

    reactor.run()


if __name__ == "__main__":
    main()
