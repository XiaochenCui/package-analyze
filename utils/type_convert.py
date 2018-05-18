import struct


def bytes_to_int(byte, byte_order='>'):
    """
    :type byte: str
    :type byte_order: str
    """
    if len(byte) == 1:
        format_flag = 'B'
    elif len(byte) == 2:
        format_flag = 'H'
    elif len(byte) == 4:
        format_flag = 'L'

    format_string = byte_order + format_flag

    return struct.unpack(format_string, byte)[0]
