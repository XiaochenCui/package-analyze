import logging
from collections import namedtuple


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
    :rtype: dict
    """
    logger.debug(data)
    logger.debug(len(data))
    dic = {
        "start": data[0:2],
        "command_flag": data[2],
        "answer_flag": data[3],
        "unique_code": data[4:21],
        "encrypto_method": data[21],
        "length": data[22:24],
        "payload": data[24:-1],
        "checksum": data[-1],
    }
    return dic


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


def get_package_type(package):
    """
    Get package's type

    :param package:
    :type package: dict
    :rtype: str
    """
    command_flag = package["command_flag"]
    answer_flag = package["answer_flag"]
    if command_flag == 0x01:
        if answer_flag == 0xFE:
            return "Login"
        return "Reply to login"
    elif command_flag == 0x02:
        if answer_flag == 0xFE:
            return "Real time status"
        return "Reply to real time status"
    elif command_flag == 0x82:
        if answer_flag == 0xFE:
            return "Control command"
        return "Reply to control command"
    return "Unknown"
