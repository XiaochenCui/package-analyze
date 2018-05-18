import datetime
import logging.config
import binascii
import json
import re
from os import linesep
import argparse

import netifaces
from autobahn.twisted.websocket import (
    WebSocketServerProtocol,
    WebSocketServerFactory,
)
from twisted.protocols import basic
from twisted.internet import stdio

from config import config
from utils.deconstruct_package import (
    deconstruct_package,
    PackageHandler,
)
from utils.type_convert import bytes_to_int


logging.config.fileConfig("config/logging_config.ini")
logger = logging.getLogger(__name__)


class UserInputProtocol(basic.LineReceiver):
    """Handle input bytestream"""

    delimiter = linesep.encode("utf8")

    def __init__(self, callback):
        self.callback = callback

    def lineReceived(self, line):
        self.callback(line)


class DebugPackageServerProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        logger.debug("Client connecting: {0}".format(request.peer))
        self.factory.protocol_pool.append(self)

    def onOpen(self):
        logger.debug("WebSocket connection open.")

    def onClose(self, wasClean, code, reason):
        logger.debug("WebSocket connection closed: {0}".format(reason))
        self.factory.protocol_pool.remove(self)


class DebugPackageServerFactory(WebSocketServerFactory):

    protocol = DebugPackageServerProtocol

    def __init__(self, interface, server_port):
        """

        :param interface: specific which interface to listen
        :type interface: string
        """
        self.interface = interface
        self.server_port = server_port

        stdio.StandardIO(UserInputProtocol(self.user_input_received))

        super(DebugPackageServerFactory, self).__init__(
            "ws://127.0.0.1:{port}".format(port=config.WEB_SOCKET_PORT)
        )
        self.protocol_pool = []

        self.data_temp = None

    def user_input_received(self, data):
        """
        Process user input

        :param data:
        :type data: bytes
        """
        # data example: 120.026.081.035.04020-192.168.003.192.60036: ##TTUJJJ563EM063163,
        data = self.package_gateway(data)
        if data:
            self.broadcast_packages(data)

    def pretreatment_data(self, data):
        if self.data_temp:
            logger.debug((self.data_temp, data))
            data = self.data_temp + data
            logger.debug(data)

        pattern = re.compile(b"(?P<source_host>.+?)\.(?P<source_port>\d{5})-(?P<dest_host>.+?)\.(?P<dest_port>\d{5}): (?P<tcp_data>.+)")
        match = pattern.match(data)
        if match:
            tcp_dic = match.groupdict()
            logger.debug('Tcp package: {}'.format(tcp_dic))
            hex_data = binascii.hexlify(tcp_dic['tcp_data'])
            logger.debug('Hex representation of package: {}'.format(hex_data))
            return tcp_dic

        logger.info('Invalid package: {}'.format(data))

    def package_gateway(self, data):
        pattern = re.compile(b"(?P<source_host>.+?)\.(?P<source_port>\d{5})-(?P<dest_host>.+?)\.(?P<dest_port>\d{5}): (?P<tcp_data>.+)")
        match = pattern.match(data)
        if match:
            tcp_dic = match.groupdict()
            logger.debug('Tcp package: {}'.format(tcp_dic))

            self.sender = self.get_sender(tcp_dic)

            package = deconstruct_package(tcp_dic['tcp_data'])
            if len(package.payload) < package.length:
                logger.info("A truncated package: {}".format(package.payload))
                self.data_temp = package.raw_data
                return

            return self.process_package(package)
        else:
            self.data_temp = self.data_temp + b'\n' + data

            package = deconstruct_package(self.data_temp)
            if len(package.payload) < package.length:
                logger.info("A truncated package: {}".format(package.payload))
                return

            return self.process_package(package)

    def broadcast_packages(self, data):
        for protocol in self.protocol_pool:
            protocol.sendMessage(data, False)

    def get_sender(self, package):
        """
        Get sender

        :param package:
        :type package: dict
        :rtype: string
        """
        if int(package["dest_port"]) == self.server_port:
            return "client"
        return "server"

    def process_package(self, package):
        # There is a bug in the program: since the tcp package are received as
        # binary data, if there is new line character in tcp package, the
        # package will be truncated to two and send to input handler
        # seperately.
        #
        # Since this problem is caused by binary security, changing the
        # separator cant't solve it.
        #
        # So we temporary deposit truncated packages and connect them later on.
        package["sender"] = self.sender

        package_handler = PackageHandler()

        package_type, timestamp = package_handler.get_package_type(package)
        vin = package['unique_code']
        package["package_type"] = package_type

        if timestamp:
            conn = package_handler.redis_conn
            key = "package_type:{}".format(vin)
            conn.hset(key, timestamp, package_type)
            conn.expire(key, 10)

        package["datetime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        package["vin"] = vin.decode()

        def split_str_by_step(string, step):
            for i in range(0, len(string), step):
                yield string[i:i + step]

        for k, v in package.items():
            if isinstance(v, int):
                v = bytes([v])
            if isinstance(v, str):
                v = v.encode("utf8")
                continue
            v = binascii.hexlify(v).decode("ascii")
            v = list(split_str_by_step(v, 2))
            v = ' '.join(v)
            package[k] = v

        data = json.dumps(package).encode("ascii")
        return data

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--interface",
        type=str,
        help="specific which interface to listen",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        help="specific which interface to listen",
    )
    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    from twisted.internet import reactor

    factory = DebugPackageServerFactory(args.interface, args.port)
    factory.protocol = DebugPackageServerProtocol

    reactor.listenTCP(config.WEB_SOCKET_PORT, factory)

    reactor.run()


if __name__ == "__main__":
    main()
