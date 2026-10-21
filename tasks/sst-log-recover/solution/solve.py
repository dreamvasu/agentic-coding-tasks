#!/usr/bin/env python3
"""
Reference recovery for sst-log-recover.

Resolves each target key to the payload written by the highest sequence number
among COMPLETE write batches, across both the sorted tables and the write-ahead
log. Reads the store byte-wise; never opens it with the engine (which would
consume the log).

Usage: solve.py [store_dir] [out_dir]   (defaults: /app/data/store  /app/output)
"""

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ldbfmt import (manifest_live_files, parse_batch, read_log, read_varint,
                    sst_entries)

IDS = ["0007", "0019", "0042", "0063", "0104", "0137",
       "0205", "0268", "0301", "0358", "0412", "0470"]

STORE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/app/data/store")
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/app/output")

TARGETS = {f"obj:{i}".encode(): i for i in IDS}


def complete_batch(payload):
    """Entries of a batch, or None if the batch is truncated (declared count > present)."""
    if len(payload) < 12:
        return None
    seq, count = struct.unpack("<QI", payload[:12])
    i, out = 12, []
    try:
        for n in range(count):
            op = payload[i]; i += 1
            kl, i = read_varint(payload, i)
            k = payload[i:i + kl]; i += kl
            if len(k) != kl:
                return None
            if op == 1:
                vl, i = read_varint(payload, i)
                v = payload[i:i + vl]; i += vl
                if len(v) != vl:
                    return None
                out.append((seq + n, 1, k, v))
            elif op == 0:
                out.append((seq + n, 0, k, None))
            else:
                return None
    except (IndexError, ValueError):
        return None
    return out if len(out) == count else None


def recover():
    best = {}                                    # key -> (seq, type, value)

    def offer(seq, typ, key, val):
        if key in TARGETS and (key not in best or seq > best[key][0]):
            best[key] = (seq, typ, val)

    # 1. sorted tables that the manifest actually references (an unreferenced .ldb
    #    left over from a crashed compaction must not be treated as live state)
    man = sorted(STORE.glob("MANIFEST-*"))
    live = manifest_live_files(man[-1].read_bytes()) if man else set()
    for ldb in sorted(STORE.glob("*.ldb")):
        if int(ldb.stem) not in live:
            continue
        for ukey, seq, typ, val in sst_entries(ldb.read_bytes()):
            offer(seq, typ, ukey, val)

    # 2. the write-ahead log. A torn record is skipped, but scanning CONTINUES past
    #    it: the records after the tear are intact and hold the newest writes.
    for log in sorted(STORE.glob("*.log")):
        for payload, crc_ok in read_log(log.read_bytes()):
            if not crc_ok:
                continue
            ents = complete_batch(payload)
            if ents is None:                     # truncated batch: never finished, discard whole
                continue
            for seq, typ, k, v in ents:
                offer(seq, typ, k, v)

    missing = [i for k, i in TARGETS.items() if k not in best or best[k][1] != 1]
    if missing:
        raise SystemExit(f"failed to recover ids: {sorted(missing)}")

    OUT.mkdir(parents=True, exist_ok=True)
    for key, doc_id in TARGETS.items():
        (OUT / f"{doc_id}.bin").write_bytes(best[key][2])
    print(f"recovered {len(TARGETS)} payloads -> {OUT}")


if __name__ == "__main__":
    recover()
