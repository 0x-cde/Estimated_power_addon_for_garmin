"""Convert an X11 xwd dump (ZPixmap, 24 or 32 bpp) to PNG, stdlib only. Usage: xwd2png.py IN.xwd OUT.png"""
import struct, sys, zlib
raw = open(sys.argv[1], "rb").read()
h = struct.unpack(">25I", raw[:100])
hsize, w, hh, byte_order, bpp, bpl, nc = h[0], h[4], h[5], h[7], h[11], h[12], h[19]
step = bpp // 8
off = hsize + nc * 12
rows = []
for y in range(hh):
    r = raw[off + y * bpl: off + y * bpl + w * step]
    row = bytearray([0])
    for x in range(w):
        b = r[x * step: x * step + step]
        row += bytes((b[2], b[1], b[0])) if byte_order == 0 else bytes(b[-3:])
    rows.append(bytes(row))
ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
open(sys.argv[2], "wb").write(b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, hh, 8, 2, 0, 0, 0))
                              + ch(b"IDAT", zlib.compress(b"".join(rows))) + ch(b"IEND", b""))
