import logging
from collections import namedtuple
import binascii


logger = logging.getLogger(__name__)


Unit = namedtuple("Unit", ["start", "end"])
START = Unit(0, 2)
COMMAND_FLAG = Unit(2, 3)
ANSWER_FLAG = Unit(3, 4)
UNIQUE_CODE = Unit(4, 21)
ENCRYPTO_METHOD = Unit(21, 22)
LENGTH = Unit(22, 24)
PAYLOAD = Unit(24, -1)


def deconstruct_package(data):
    """
    Deconstruct a package, return d dict

    :param data: package content
    :type data: bytes
    :rtype: Bunch
    """
    from bunch import Bunch
    package = Bunch()
    package.start = data[0:2]
    from utils.type_convert import bytes_to_int
    package.command_flag = data[2]
    package.answer_flag = data[3]
    package.unique_code = data[4:21]
    package.encrypto_method = data[21]
    package.length = bytes_to_int(data[22:24])
    package.payload = data[24:-1]
    package.checksum = data[-1]
    package.raw_data = data
    return package


def deconstruct_hex_package(data):
    """
    Deconstruct a package in hex format

    :param data: package content
    :type data: str
    :rtype: dict
    """
    dic = {
        "start": data[0:4],
        "command_flag": data[4:6],
        "answer_flag": data[6:8],
        "unique_code": data[8:42],
        "encrypto_method": data[42:44],
        "length": data[44:48],
        "payload": data[48:-2],
        "checksum": data[-2:],
    }
    return dic


class PackageHandler():

    def __init__(self):
        self.redis_conn = self.get_redis_conn()

    def get_redis_conn(self):
        import redis
        from config import config
        conn = redis.StrictRedis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
        )
        return conn

    def establish_db_conn(self):
        conn = psycopg2.connect(
            dbname='dfjk-fuel',
            user='postgres',
            host='db',
        )
        self.db_conn = conn

    def get_package_type(self, package):
        """
        Get package's type

        :param package:
        :type package: dict
        :rtype: str
        """
        command_flag = package["command_flag"]
        answer_flag = package["answer_flag"]

        payload = package['payload']
        vin = package['unique_code']
        timestamp = payload[:6]

        if answer_flag != 0xFE and len(payload) == 6:
            # This is a response package
            conn = self.redis_conn
            key = "package_type:{}".format(vin)
            values = conn.hgetall(key)
            package_type = conn.hget(key, timestamp)
            conn.hdel(key, timestamp)

            if package_type is None:
                logger.info("Cannnot find request package for response package {}".format(
                    binascii.hexlify(package["raw_data"]),
                ))
                return "Unknown", None

            return "Reply to " + package_type.decode(), None

        package_type = "Unknown"

        if command_flag == 0x01:
            package_type = "Login"

        elif command_flag == 0x02:
            package_type = "Real time status"

        elif command_flag == 0x82:
            command_id = package['payload'][6]

            if command_id == 0x80:
                package_type = "Lock command"
            elif command_id == 0x81:
                package_type = "Lock command (limit rotate speed)"
            elif command_id == 0x82:
                package_type = "Lock command (limit torque)"
            elif command_id == 0x90:
                package_type = "Unlock command"

            elif command_id == 0x55:
                package_type = "Bind command"
            elif command_id == 0xAA:
                package_type = "Unbind command"

        elif command_flag == 0x09:
            command_id = package['payload'][6]

            if command_id == 0x55:
                package_type = "Report bind result"
            elif command_id == 0xAA:
                package_type = "Report unbind result"
            elif command_id == 0x80:
                package_type = "Report lock result"
            elif command_id == 0x81:
                package_type = "Report limite rotate speed result"
            elif command_id == 0x82:
                package_type = "Report limite torque result"
            elif command_id == 0x90:
                package_type = "Report unlock result"

        return package_type, timestamp
