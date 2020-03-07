import struct

#from ryu.lib.packet import packet_base


#class nsh(packet_base.PacketBase):
class nsh():


    """
     0                   1                   2                   3
      0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |Ver|O|U|    TTL    |   Length  |U|U|U|U|MD Type| Next Protocol |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |          Service Path Identifier (SPI)        | Service Index |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

    """
    _PACK_STR ='!BBBBI'
    _MIN_LEN = struct.calcsize(_PACK_STR)

    def __init__(self, ver=0, O=0,ttl=63 ,length=6, md = 1, np=3, 
                 spi=0, si= 255):
        super(nsh, self).__init__()
        self.ver = ver
        self.O = O
        self.ttl = ttl
        self.length = length
        self.md = md
        self.np = np
        self.spi = spi
        self.si = si

    @classmethod
    def parser(cls, buf):
        (ver_O_U_ttl4, ttl2_len, U4_md, np, spisi) = struct.unpack_from(cls._PACK_STR, buf)
        ver = ver_O_U_ttl4 >> 6
        O = ver_O_U_ttl4 & 0x20
        O >>= 5
        ttl = struct.unpack('!H',struct.pack('!B',(ver_O_U_ttl4  & 0x0f)) + struct.pack('!B',(ttl2_len  & 0xc0)))[0] >> 6
        length = ttl2_len & 0x3f
        md = U4_md & 0x0f
        np = np
        spi = (spisi & 0xffffff00) >> 8
        si = (spisi & 0x000000ff)

        return (cls(ver, O, ttl, length, md, np, spi, si),np,buf[4*length:])
