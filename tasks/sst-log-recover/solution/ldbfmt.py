"""Minimal LevelDB log-format writer/reader. Formats per doc/log_format.md + write_batch."""
import struct

_POLY = 0x82F63B78
_TAB = []
for i in range(256):
    c = i
    for _ in range(8):
        c = (c >> 1) ^ (_POLY if c & 1 else 0)
    _TAB.append(c)

def crc32c(data, crc=0):
    c = crc ^ 0xFFFFFFFF
    for b in data:
        c = _TAB[(c ^ b) & 0xFF] ^ (c >> 8)
    return c ^ 0xFFFFFFFF

MASK_DELTA = 0xA282EAD8
def mask(c):    return (((c >> 15) | (c << 17)) + MASK_DELTA) & 0xFFFFFFFF
def unmask(m):  r = (m - MASK_DELTA) & 0xFFFFFFFF; return ((r >> 17) | (r << 15)) & 0xFFFFFFFF

BLOCK = 32768
HDR = 7
FULL, FIRST, MIDDLE, LAST = 1, 2, 3, 4

def varint(n):
    out = bytearray()
    while n >= 0x80:
        out.append((n & 0x7F) | 0x80); n >>= 7
    out.append(n); return bytes(out)

def read_varint(buf, i):
    r = s = 0
    while True:
        b = buf[i]; i += 1
        r |= (b & 0x7F) << s
        if not (b & 0x80): return r, i
        s += 7

def write_batch(seq, entries):
    """entries: list of (op, key, value) where op is 'put' or 'del'."""
    out = bytearray(struct.pack('<QI', seq, len(entries)))
    for op, k, v in entries:
        if op == 'put':
            out += b'\x01' + varint(len(k)) + k + varint(len(v)) + v
        else:
            out += b'\x00' + varint(len(k)) + k
    return bytes(out)

class LogWriter:
    def __init__(self): self.buf = bytearray()
    def _emit(self, rtype, payload, bad_crc=False):
        c = mask(crc32c(bytes([rtype]) + payload))
        if bad_crc: c ^= 0xFFFFFFFF
        self.buf += struct.pack('<IHB', c, len(payload), rtype) + payload
    def add(self, payload, bad_crc=False):
        """Fragment payload across 32K blocks exactly as leveldb does."""
        first = True
        while True:
            left = BLOCK - (len(self.buf) % BLOCK)
            if left < HDR:
                self.buf += b'\x00' * left; left = BLOCK
            avail = left - HDR
            n = min(avail, len(payload))
            end = (n == len(payload))
            rtype = (FULL if (first and end) else FIRST if first else LAST if end else MIDDLE)
            self._emit(rtype, payload[:n], bad_crc and first)
            payload = payload[n:]; first = False
            if end: break
    def pad_to_block(self):
        """Zero-fill to the next 32K boundary. A zero header means "skip to the next block"
        to both leveldb's reader and ours, so this is a safe alignment primitive."""
        left = BLOCK - (len(self.buf) % BLOCK)
        if left != BLOCK:
            self.buf += b"\x00" * left

    def bytes(self): return bytes(self.buf)

def read_log(data, verify=True):
    """Yield (payload, ok) per logical record, skipping block padding."""
    off = 0; frag = bytearray(); frag_ok = True
    while off + HDR <= len(data):
        if BLOCK - (off % BLOCK) < HDR:
            off += BLOCK - (off % BLOCK); continue
        c, ln, t = struct.unpack('<IHB', data[off:off + HDR])
        if t == 0 and ln == 0:
            off += BLOCK - (off % BLOCK); continue
        payload = data[off + HDR:off + HDR + ln]
        ok = (not verify) or (unmask(c) == crc32c(bytes([t]) + payload))
        off += HDR + ln
        if t == FULL:
            yield bytes(payload), ok
        elif t == FIRST:
            frag = bytearray(payload); frag_ok = ok
        elif t == MIDDLE:
            frag += payload; frag_ok &= ok
        elif t == LAST:
            frag += payload; yield bytes(frag), (frag_ok and ok); frag = bytearray()

def parse_batch(payload):
    seq, count = struct.unpack('<QI', payload[:12])
    i = 12; out = []
    for n in range(count):
        op = payload[i]; i += 1
        kl, i = read_varint(payload, i); k = payload[i:i + kl]; i += kl
        if op == 1:
            vl, i = read_varint(payload, i); v = payload[i:i + vl]; i += vl
            out.append((seq + n, 'put', k, v))
        else:
            out.append((seq + n, 'del', k, None))
    return out


def snappy_decompress(data):
    """Pure-python snappy block decoder (leveldb compresses SST blocks with it)."""
    ulen, i = read_varint(data, 0)
    out = bytearray()
    while i < len(data):
        tag = data[i]; i += 1
        t = tag & 0x03
        if t == 0:                                  # literal
            n = tag >> 2
            if n < 60:
                ln = n + 1
            else:
                extra = n - 59
                ln = int.from_bytes(data[i:i + extra], "little") + 1
                i += extra
            out += data[i:i + ln]; i += ln
        else:
            if t == 1:
                ln = 4 + ((tag >> 2) & 0x07)
                off = ((tag >> 5) << 8) | data[i]; i += 1
            elif t == 2:
                ln = (tag >> 2) + 1
                off = int.from_bytes(data[i:i + 2], "little"); i += 2
            else:
                ln = (tag >> 2) + 1
                off = int.from_bytes(data[i:i + 4], "little"); i += 4
            start = len(out) - off
            for k in range(ln):
                out.append(out[start + k])          # byte-wise: copies may overlap
    if len(out) != ulen:
        raise ValueError(f"snappy length mismatch {len(out)} != {ulen}")
    return bytes(out)


# ---------------------------------------------------------------- SST (.ldb) reader
SST_MAGIC = 0xDB4775248B80FB57

def _blockhandle(buf, i):
    off, i = read_varint(buf, i)
    size, i = read_varint(buf, i)
    return off, size, i

def _block_entries(block):
    """Yield (internal_key, value) from an uncompressed data/index block."""
    n = struct.unpack('<I', block[-4:])[0]
    restarts_off = len(block) - 4 - 4 * n
    i, last = 0, b''
    while i < restarts_off:
        shared, i = read_varint(block, i)
        non_shared, i = read_varint(block, i)
        vlen, i = read_varint(block, i)
        if shared == 0 and non_shared == 0 and vlen == 0:
            break
        key = last[:shared] + block[i:i + non_shared]; i += non_shared
        val = block[i:i + vlen]; i += vlen
        last = key
        yield key, val

def _read_block(data, off, size, verify=True):
    raw = data[off:off + size]
    ctype = data[off + size]
    stored = struct.unpack('<I', data[off + size + 1:off + size + 5])[0]
    if verify and unmask(stored) != crc32c(raw + bytes([ctype])):
        raise ValueError(f"block crc mismatch at {off}")
    if ctype == 1:
        return snappy_decompress(raw)
    if ctype != 0:
        raise ValueError(f"unsupported block compression type {ctype}")
    return raw

def sst_entries(data, verify=True):
    """Yield (user_key, seq, type, value) for every entry in an .ldb file. type 1=put 0=del."""
    if struct.unpack('<Q', data[-8:])[0] != SST_MAGIC:
        raise ValueError("not an sst: bad magic")
    footer = data[-48:-8]
    _, _, i = _blockhandle(footer, 0)          # metaindex handle (unused)
    ioff, isize, _ = _blockhandle(footer, i)   # index handle
    index = _read_block(data, ioff, isize, verify)
    for _, handle in _block_entries(index):
        boff, bsize, _ = _blockhandle(handle, 0)
        for ikey, val in _block_entries(_read_block(data, boff, bsize, verify)):
            tag = struct.unpack('<Q', ikey[-8:])[0]
            yield ikey[:-8], tag >> 8, tag & 0xFF, val

# ------------------------------------------------------------ MANIFEST (VersionEdit)
def manifest_live_files(data):
    """File numbers added minus deleted across every VersionEdit record in the MANIFEST."""
    live = set()
    for payload, ok in read_log(data):
        if not ok:
            continue
        i = 0
        while i < len(payload):
            tag, i = read_varint(payload, i)
            if tag == 1:                                    # comparator name (string)
                n, i = read_varint(payload, i); i += n
            elif tag in (2, 3, 4, 9):                       # lognum / nextfile / lastseq / prevlog
                _, i = read_varint(payload, i)
            elif tag == 5:                                   # compact pointer: level + internal key
                _, i = read_varint(payload, i)
                n, i = read_varint(payload, i); i += n
            elif tag == 6:                                  # deleted file: level, number
                _, i = read_varint(payload, i)
                num, i = read_varint(payload, i); live.discard(num)
            elif tag == 7:                                  # new file: level, number, size, smallest, largest
                _, i = read_varint(payload, i)
                num, i = read_varint(payload, i)
                _, i = read_varint(payload, i)
                for _k in range(2):
                    n, i = read_varint(payload, i); i += n
                live.add(num)
            else:
                break
    return live
