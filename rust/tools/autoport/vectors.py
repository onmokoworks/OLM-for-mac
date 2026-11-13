"""ABI vector generation and packing. No reference algorithm is implemented here."""
import copy
import random
import struct

FLOAT32 = [0, 0x80000000, 1, 0x80000001, 0x007fffff, 0x00800000,
           0x3f000000, 0x3f800000, 0xbf800000, 0x7f7fffff, 0x7f800000,
           0xff800000, 0x7fc01234, 0x7f801234, 0xffc01234]


def blob(data):
    return {"size": len(data), "hex": bytes(data).hex()}


def ptr(name, offset=0):
    return {"type": "ptr", "buffer": name, "offset": offset}


def scalar_vectors(abi, seed, count=64):
    rng = random.Random(seed)
    pools = []
    for kind in abi["args"]:
        if kind == "ptr":
            raise ValueError("pointer ABI requires recorded vectors or a fixture generator")
        width = int(kind[1:])
        if kind == "f32":
            values = FLOAT32
        elif kind == "f64":
            values = [0, 1 << 63, 1, (1 << 52)-1, 1 << 52, 0x3ff0000000000000,
                      0x7ff0000000000000, 0xfff0000000000000, 0x7ff8000000001234,
                      0x7ff0000000001234]
        else:
            values = [0, 1, 2, 3, 4, 7, 8, 15, 16, 31, 32, (1 << (width-1))-1,
                      1 << (width-1), (1 << width)-1]
        pools.append(values)
    for i in range(max(count, max(map(len, pools), default=1))):
        args = [{"type": kind, "bits": hex(pool[i] if i < len(pool) else rng.getrandbits(int(kind[1:])))}
                for kind, pool in zip(abi["args"], pools)]
        yield {"label": f"scalar-{i}", "buffers": {}, "args": args, "return": abi["return"]}


def color_keep(depth, seed):
    rng = random.Random(seed)
    # Actual decompiled callback layout: count @0x24; contiguous float ARGB @0x28.
    # Sizes exercise loop unrolling and tails. No expected output is generated.
    for count in [-1, 0, 1, 2, 3, 4, 5, 7, 8, 9, 24]:
        for variant in range(18):
            words = [FLOAT32[(variant+j) % len(FLOAT32)] for j in range(4)]
            if depth == 32:
                pixel = struct.pack("<4I", *words)
                palette = pixel if variant % 3 == 0 else struct.pack("<4f", *[rng.random() for _ in range(4)])
            else:
                max_value = 255 if depth == 8 else 32768
                channels = [rng.randrange(max_value+1) for _ in range(4)]
                if variant == 0:
                    channels = [0]*4
                elif variant == 1:
                    channels = [max_value]*4
                pixel = struct.pack("<4B" if depth == 8 else "<4H", *channels)
                palette = (struct.pack("<4f", *[v/max_value for v in channels])
                           if variant % 3 == 0 else struct.pack("<4I", *words))
            context = bytearray(0x28 + max(1, count)*16)
            struct.pack_into("<i", context, 0x24, count)
            for n in range(max(1, count)):
                context[0x28+n*16:0x38+n*16] = palette if n == max(0, count-1) else bytes(16)
            yield {"label": f"pf{depth}-count{count}-v{variant}",
                   "buffers": {"context": blob(context), "input": blob(pixel),
                               "output": {"size": len(pixel), "fill": 0xa5}},
                   "args": [ptr("context"), {"type":"u64","value":0}, {"type":"u64","value":0},
                            ptr("input"), ptr("output")], "return": "u64"}


def toon(kind, depth, seed):
    rng = random.Random(seed)
    for i in range(64):
        if depth == 32:
            pixel = struct.pack("<4I", *[FLOAT32[(i+j)%len(FLOAT32)] if i < 20 else rng.getrandbits(32)
                                       for j in range(4)])
        else:
            pixel = struct.pack("<4B" if depth == 8 else "<4H",
                *[([0, 1, 127, 255] if depth == 8 else [0, 1, 32768, 65535])[j]
                  if i == 0 else rng.getrandbits(depth) for j in range(4)])
        if kind == "copy":
            buffers = {"input": blob(pixel), "output": blob(bytes([0xa5])*8+pixel+bytes([0xa5])*8)}
            args = [ptr("input"), ptr("output", 8)]
            if i == 1:
                args[0] = {"type":"ptr","value":0}
            if i == 2:
                args[1] = {"type":"ptr","value":0}
            if i == 3:  # aliasing is part of the sequential store contract
                args = [ptr("output", 8), ptr("output", 8)]
            if i == 4:
                args = [ptr("output", 8), ptr("output", 8 + (1 if depth == 8 else depth//8))]
        else:
            buffers = {"input": blob(pixel), "output": {"size": 16, "fill": 0xa5}}
            args = [ptr("output", j*4) for j in range(4)] + [ptr("input")]
        yield {"label": f"{kind}{depth}-{i}", "buffers": buffers, "args": args, "return": "void"}


def generate(contract, seed):
    fixture = contract.get("fixture", "scalar")
    if fixture.startswith("color"):
        rows = list(color_keep(int(fixture[5:]), seed))
    elif fixture.startswith("copy") or fixture.startswith("unpack"):
        kind = "copy" if fixture.startswith("copy") else "unpack"
        rows = list(toon(kind, int(fixture[len(kind):]), seed))
    elif fixture == "scalar":
        rows = list(scalar_vectors(contract["abi"], seed))
    elif fixture == "recorded":
        rows = []
    else:
        raise ValueError(f"unknown fixture {fixture}")
    rows.extend(copy.deepcopy(contract.get("recorded", [])))
    if not rows:
        raise ValueError("empty vector corpus cannot verify a function")
    for row in rows:
        if [a["type"] for a in row["args"]] != contract["abi"]["args"] or row["return"] != contract["abi"]["return"]:
            raise ValueError("vector ABI differs from the reviewed contract")
    return rows


def pack(rows, module, rva, fma):
    """One guarded arena, disjoint initial state per call; preserve alias relationships.

    A self-pointer anchor allows address normalization across ASLR. All pointer
    offsets and non-pointer bytes (input bytes, guard gaps and padding) are compared.
    """
    arena = bytearray()
    offsets = []
    pointers = []
    calls = []
    for row in rows:
        locations = {}
        for name, buf in row.get("buffers", {}).items():
            if "file" in buf:
                raise ValueError("recorded vectors must inline bytes as hex")
            arena.extend(bytes([0xd3])*((-len(arena)) % 16+16))
            locations[name] = len(arena)
            data = bytearray([buf.get("fill", 0)])*buf["size"]
            init = bytes.fromhex(buf.get("hex", ""))
            if len(init) > len(data):
                raise ValueError("initializer exceeds buffer")
            data[:len(init)] = init
            arena.extend(data)
            arena.extend(bytes([0xd3])*16)
        for name, buf in row.get("buffers", {}).items():
            for p in buf.get("pointers", []):
                if not 0 <= p["offset"] <= buf["size"]-8:
                    raise ValueError("invalid relocation")
                if not 0 <= p.get("addend",0) <= row["buffers"][p["buffer"]]["size"]:
                    raise ValueError("invalid relocation target")
                pointers.append({"offset":locations[name]+p["offset"], "buffer":"arena",
                                 "addend":locations[p["buffer"]]+p.get("addend",0)})
        args = copy.deepcopy(row["args"])
        for arg in args:
            if "buffer" in arg:
                if not 0 <= arg.get("offset", 0) <= row["buffers"][arg["buffer"]]["size"]:
                    raise ValueError("argument outside vector buffer")
                arg["offset"] = locations[arg["buffer"]] + arg.get("offset",0)
                arg["buffer"] = "arena"
        calls.append({"label":row["label"], "rva":hex(rva), "args":args, "return":row["return"]})
        offsets.append(locations)
    if len(arena) > 8*1024*1024 or len(rows) > 4096:
        raise ValueError("corpus exceeds bounded comparison size")
    if pointers:
        arena.extend(bytes([0xd3])*16)
        pointers.append({"offset":len(arena),"buffer":"arena","addend":0})
        arena.extend(bytes(8))
    return {"schema_version":1, "module":str(module), "fma":fma,
            "buffers":{"arena":{**blob(arena), "pointers":pointers}} if arena else {}, "calls":calls}
