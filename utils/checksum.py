from functools import reduce


def bcc(data):
    """
    Calculate BCC (Block Check Character) checksum for data

    :param data:
    :type data: string
    :return: BCC checksum
    :rtype: int
    """
    return reduce(lambda a,b: a^b, bytearray(data))
