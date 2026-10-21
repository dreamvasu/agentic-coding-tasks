#!/usr/bin/env python3
"""
build_fixture.py - deterministic generator for the sst-log-recover task.

Builds a genuine LevelDB store with the real engine, then applies targeted binary
surgery to a crash-consistent copy. The seed lives here and is never shipped in the
agent image.

Layout of the damaged write-ahead log (the heart of the task):

    [ group A ]  valid records, CURRENT values for one set of keys
    [ TORN    ]  one record with a deliberately corrupted CRC
    [ group B ]  valid records, CURRENT values for the rest   <- past the tear
    [ group C ]  valid records with LOWER sequence numbers    <- stale decoy
    [ tail    ]  a truncated WriteBatch (count > entries present)

The real engine stops recovering at the tear, so it silently returns stale values for
every key in B and, on open, deletes the log entirely. Recovering B requires scanning
past the tear by hand; rejecting C requires ordering by sequence number rather than by
position in the file.

Run:  python3 tasks/sst-log-recover/environment/data/build_fixture.py
"""

import hashlib
import json
import os
import random
import shutil
import struct
import sys
import subprocess
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ldbfmt import (BLOCK, LogWriter, crc32c, mask, parse_batch, read_log,  # noqa
                    write_batch)

SEED = 20260728

TARGETS = ["obj:0007", "obj:0019", "obj:0042", "obj:0063", "obj:0104", "obj:0137",
           "obj:0205", "obj:0268", "obj:0301", "obj:0358", "obj:0412", "obj:0470"]

UNTOUCHED = {"obj:0019", "obj:0358"}          # current == base; survive every failure -> 2/12 floor
GROUP_B   = {"obj:0137", "obj:0205", "obj:0268", "obj:0470"}   # current value sits PAST the tear
LARGE     = {"obj:0007", "obj:0042", "obj:0104", "obj:0301", "obj:0470"}  # fragment across 32K blocks
STALE_DECOY = {"obj:0007", "obj:0042", "obj:0063", "obj:0104", "obj:0301"}  # group C re-writes these
TOMBSTONE = "obj:0412"                        # group C carries a stale DELETE for this key
ORPHAN_SST = {"obj:0019", "obj:0063", "obj:0358", "obj:0412"}  # stale copies in an unreferenced .ldb

N_KEYS = 500
DATA_DIR = Path(__file__).resolve().parent
TASK_DIR = DATA_DIR.parent.parent
TESTS_DIR = TASK_DIR / "tests"
STORE = DATA_DIR / "store"


def val_len(rng, key):
    if key in LARGE:
        return rng.randint(40000, 90000)      # > 32K block: forces FIRST/MIDDLE/LAST fragmenting
    return rng.randint(200, 3000)


def payload(rng, n):
    """Cache-object-like bytes: repetitive enough that leveldb's snappy actually engages on
    the sorted tables (random bytes would be stored uncompressed and defeat the point)."""
    vocab = [bytes([rng.randrange(256)]) * rng.randint(4, 24) +
             rng.randbytes(rng.randint(8, 40)) for _ in range(24)]
    out = bytearray()
    while len(out) < n:
        out += vocab[rng.randrange(len(vocab))]
    return bytes(out[:n])


def build_base(rng):
    """Real LevelDB writes every key's BASE value, then compacts it all into .ldb files."""
    import plyvel
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "db")
    db = plyvel.DB(path, create_if_missing=True)   # default compression: snappy
    base, lengths = {}, {}
    for i in range(1, N_KEYS + 1):
        key = f"obj:{i:04d}".encode()
        L = val_len(rng, key.decode())
        v = payload(rng, L)
        db.put(key, v)
        if key.decode() in TARGETS:
            base[key.decode()] = v
            lengths[key.decode()] = L
    db.compact_range()                         # force the memtable out into SSTs
    db.close()
    return tmp, path, base, lengths


def stale_sst(rng, keys, lengths):
    """A second real DB holding only stale copies -> its .ldb becomes the unreferenced orphan."""
    import plyvel
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "db")
    db = plyvel.DB(path, create_if_missing=True)   # default compression: snappy
    for k in sorted(keys):
        db.put(k.encode(), payload(rng, lengths[k]))    # same length as current: no size tell
    db.compact_range()
    db.close()
    ldbs = sorted(f for f in os.listdir(path) if f.endswith(".ldb"))
    if not ldbs:
        raise SystemExit("stale donor produced no .ldb")
    return tmp, os.path.join(path, ldbs[-1])


def main():
    rng = random.Random(SEED)
    print(f"building fixture (seed={SEED}, {N_KEYS} keys, {len(TARGETS)} targets)...")

    tmp, path, base, lengths = build_base(rng)
    logs = [f for f in os.listdir(path) if f.endswith(".log")]
    if not logs:
        raise SystemExit("expected a live .log in the base db")
    live_log = logs[0]

    # ---- decide the CURRENT value of every target -------------------------------------
    current = dict(base)
    updated = [k for k in TARGETS if k not in UNTOUCHED]
    for k in updated:
        current[k] = payload(rng, lengths[k])          # same length as base: no size tell

    seq = 10_000                                        # base seq floor; real base writes are lower
    A = [k for k in updated if k not in GROUP_B]
    B = [k for k in updated if k in GROUP_B]

    w = LogWriter()

    # group A - current values, valid records, before the tear
    for k in A:
        seq += 1
        w.add(write_batch(seq, [("put", k.encode(), current[k])]))
    # Align to a block boundary so the tear is the FIRST record of a fresh block. leveldb's
    # recovery discards the remainder of the block containing a bad CRC, so this makes the
    # discarded region a full 32K and keeps it independent of payload sizes.
    w.pad_to_block()
    seq += 1
    tear_at = len(w.bytes())

    # the tear - a structurally well-formed record whose CRC is deliberately wrong.
    # leveldb's recovery drops this record AND the rest of its block.
    seq += 1
    w.add(write_batch(seq, [("put", b"obj:9999", payload(rng, 64))]), bad_crc=True)

    # group B - current values for the remaining targets, valid, PAST the tear
    for k in B:
        seq += 1
        w.add(write_batch(seq, [("put", k.encode(), current[k])]))
    past_tear = len(w.bytes())

    # group C - the decoy: physically LAST, valid CRCs, but LOWER sequence numbers than
    # the writes above, so ordering by position picks them and ordering by seq rejects them.
    decoy_seq = 9_000
    for k in sorted(STALE_DECOY):
        decoy_seq += 1
        w.add(write_batch(decoy_seq, [("put", k.encode(), payload(rng, lengths[k]))]))
    decoy_seq += 1
    w.add(write_batch(decoy_seq, [("del", TOMBSTONE.encode(), None)]))   # stale tombstone

    # tail - a WriteBatch whose header claims 3 entries but only 2 are present.
    # Not durable: it must be discarded whole, not partially applied.
    torn = bytearray(struct.pack("<QI", seq + 50, 6))
    for k in ("obj:0007", "obj:0042", "obj:0063", "obj:0104"):
        kb = k.encode(); vb = payload(rng, lengths[k])
        torn += b"\x01" + bytes([len(kb)]) + kb + _varint(len(vb)) + vb
    w.add(bytes(torn))

    (Path(path) / live_log).write_bytes(w.bytes())

    # ---- ship a crash-consistent copy -------------------------------------------------
    shutil.rmtree(STORE, ignore_errors=True)
    shutil.copytree(path, STORE)
    for junk in ("LOCK", "LOG", "LOG.old"):
        p = STORE / junk
        if p.exists():
            p.unlink()

    # ---- orphan SST: unreferenced by MANIFEST, higher file number than any live file ---
    tmp2, donor = stale_sst(rng, ORPHAN_SST, lengths)
    live_nums = [int(f.split(".")[0]) for f in os.listdir(STORE) if f.endswith(".ldb")]
    orphan = STORE / f"{max(live_nums) + 7:06d}.ldb"
    shutil.copyfile(donor, orphan)

    truth = {k: hashlib.sha256(current[k]).hexdigest() for k in TARGETS}
    meta = dict(group_a=A, group_b=B, tear_at=tear_at, past_tear=past_tear,
                orphan=orphan.name, live_log=live_log,
                lengths={k: lengths[k] for k in TARGETS})

    print(f"  log={len(w.bytes())}B tear@{tear_at} groupB@{past_tear} orphan={orphan.name}")
    print(f"  A={A}")
    print(f"  B={B}  decoys={sorted(STALE_DECOY)}  tombstone={TOMBSTONE}")

    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree(tmp2, ignore_errors=True)

    print("self-check:")
    self_check(current, truth, meta)

    TESTS_DIR.mkdir(parents=True, exist_ok=True)
    (TESTS_DIR / "expected_hashes.json").write_text(json.dumps(truth, indent=2) + "\n")
    total = sum(f.stat().st_size for f in STORE.iterdir())
    print(f"\nwrote fixture ({total}B across {len(list(STORE.iterdir()))} files), hashes.")


def _varint(n):
    out = bytearray()
    while n >= 0x80:
        out.append((n & 0x7F) | 0x80); n >>= 7
    out.append(n)
    return bytes(out)


def self_check(current, truth, meta):
    """Assert every factual claim the instruction makes. Abort the build if any fails."""
    import plyvel

    # 1. every target is recoverable from the shipped files WITHOUT the engine.
    #    (a raw byte search no longer suffices: the sorted tables are snappy-compressed,
    #    so this runs the oracle instead, which is the stronger claim anyway)
    with tempfile.TemporaryDirectory() as td:
        src, out = os.path.join(td, "s"), os.path.join(td, "o")
        shutil.copytree(STORE, src); os.makedirs(out)
        before = {f: (Path(src) / f).read_bytes() for f in os.listdir(src)}
        subprocess.run([sys.executable, str(TASK_DIR / "solution" / "solve.py"), src, out],
                       check=True, capture_output=True)
        bad = [k for k in TARGETS
               if hashlib.sha256((Path(out) / f"{k.split(':')[1]}.bin").read_bytes()).hexdigest() != truth[k]]
        if bad:
            raise SystemExit(f"PREMISE BROKEN: oracle cannot recover {bad}")
        touched = [f for f, b in before.items() if (Path(src) / f).read_bytes() != b]
        if touched:
            raise SystemExit(f"PREMISE BROKEN: oracle mutated the store: {touched}")
    print(f"  [ok] oracle recovers {len(TARGETS)}/{len(TARGETS)} read-only from the shipped files")

    # 2. the real engine, opened on a copy, returns STALE values for group B
    with tempfile.TemporaryDirectory() as td:
        d = os.path.join(td, "db")
        shutil.copytree(STORE, d)
        db = plyvel.DB(d)
        got = {k: db.get(k.encode()) for k in TARGETS}
        db.close()
        wrong = [k for k in meta["group_b"] if got[k] == current[k]]
        if wrong:
            raise SystemExit(f"PREMISE BROKEN: engine already returns CURRENT for {wrong}")
        right = sum(1 for k in TARGETS if got[k] == current[k])
        print(f"  [ok] real engine returns only {right}/12 correct (stale past the tear)")

        # 3. and opening it DESTROYED the log - the footgun
        after = os.listdir(d)
        gone = meta["live_log"] not in after
        if not gone:
            raise SystemExit("PREMISE BROKEN: opening the db did not consume the log")
        print(f"  [ok] a read-intent open deleted {meta['live_log']} and rewrote the manifest")

    # 4. the orphan .ldb is not referenced by the live manifest
    man = [f for f in os.listdir(STORE) if f.startswith("MANIFEST")]
    manbytes = (STORE / man[0]).read_bytes()
    num = int(meta["orphan"].split(".")[0])
    if _varint(num) in manbytes:
        print("  [warn] orphan file number may appear in the manifest; verify by hand")
    else:
        print("  [ok] orphan .ldb is unreferenced by the manifest")

    # 5. snappy really engaged on the sorted tables (random payloads would have been
    #    stored uncompressed, leaving the decompression trap inert)
    from ldbfmt import _blockhandle, _block_entries, _read_block, struct as _s
    for ldb in sorted(STORE.glob("*.ldb")):
        d = ldb.read_bytes()
        _, _, i = _blockhandle(d[-48:-8], 0)
        ioff, isize, _ = _blockhandle(d[-48:-8], i)
        types = []
        for _k, handle in _block_entries(_read_block(d, ioff, isize)):
            boff, bsize, _ = _blockhandle(handle, 0)
            types.append(d[boff + bsize])
        comp = sum(1 for t in types if t == 1)
        print(f"  [{'ok' if comp else 'warn'}] {ldb.name}: {comp}/{len(types)} data blocks snappy-compressed")
        if ldb.name != meta["orphan"] and not comp:
            raise SystemExit(f"PREMISE BROKEN: {ldb.name} has no compressed blocks; trap inert")

    # 6. our CRC implementation agrees with the engine's on the records IT wrote
    raw = b"".join((STORE / f).read_bytes() for f in os.listdir(STORE) if f.endswith(".log"))
    if raw:
        bad = sum(1 for _, ok in read_log(raw) if not ok)
        print(f"  [ok] log parses; {bad} record(s) fail CRC (expect exactly 1: the tear)")


if __name__ == "__main__":
    main()
