from utils.checksum import bcc


class TestChecksum(object):

    def test_bcc(self):
        data = 'A437F6F8CD'
        assert bcc(data.decode('hex')) == 0x50
        data = '1700FF7B00011100FFFFFFFF500000010600020000041100'
        assert bcc(data.decode('hex')) == 0xC3
