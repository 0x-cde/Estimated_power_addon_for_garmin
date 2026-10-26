"""Side-by-side montage of PNG crops (stdlib only). Usage: montage.py OUT.png X Y W H IN1.png IN2.png ..."""
import struct, sys, zlib
def read(p):
    d = open(p, "rb").read(); w, h = struct.unpack(">II", d[16:24]); i = 8; idat = b""
    while i < len(d):
        l = struct.unpack(">I", d[i:i+4])[0]; t = d[i+4:i+8]
        if t == b"IDAT": idat += d[i+8:i+8+l]
        i += 12 + l
    raw = zlib.decompress(idat); st = w * 3 + 1
    return w, h, [raw[y*st+1:(y+1)*st] for y in range(h)]
out, x, y, cw, ch = sys.argv[1], *map(int, sys.argv[2:6]); ins = sys.argv[6:]
crops = []
for p in ins:
    w, h, rows = read(p)
    crops.append([r[x*3:(x+cw)*3].ljust(cw*3, b"\0") for r in rows[y:y+ch]])
gap = b"\xff\xff\xff" * 10
rows = [b"\0" + gap.join(c[i] for c in crops) for i in range(ch)]
W = cw * len(crops) + 10 * (len(crops) - 1)
c = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
open(out, "wb").write(b"\x89PNG\r\n\x1a\n" + c(b"IHDR", struct.pack(">IIBBBBB", W, ch, 8, 2, 0, 0, 0)) + c(b"IDAT", zlib.compress(b"".join(rows))) + c(b"IEND", b""))
