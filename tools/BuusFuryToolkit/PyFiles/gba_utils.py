"""Shared GBA ROM utilities: LZ77, .tbl encoding, string helpers."""


def lz77_decompress(data: bytes, offset: int = 0) -> bytes:
    """Decompress Nintendo GBA LZ77 (type 0x10) data."""
    if data[offset] != 0x10:
        raise ValueError(f"Not an LZ77 block (expected 0x10, got 0x{data[offset]:02X})")
    decompressed_size = data[offset + 1] | (data[offset + 2] << 8) | (data[offset + 3] << 16)
    out = bytearray()
    i = offset + 4
    while len(out) < decompressed_size:
        flags = data[i]
        i += 1
        for bit in range(7, -1, -1):
            if len(out) >= decompressed_size:
                break
            if (flags >> bit) & 1:
                # Back-reference
                b0 = data[i]; b1 = data[i + 1]
                i += 2
                length = ((b0 >> 4) & 0xF) + 3
                disp = (((b0 & 0xF) << 8) | b1) + 1
                for _ in range(length):
                    out.append(out[len(out) - disp])
            else:
                out.append(data[i])
                i += 1
    return bytes(out)


def lz77_compress(data: bytes) -> bytes:
    """Compress bytes using Nintendo GBA LZ77 (type 0x10)."""
    size = len(data)
    header = bytes([0x10, size & 0xFF, (size >> 8) & 0xFF, (size >> 16) & 0xFF])
    out = bytearray(header)
    i = 0
    while i < size:
        flag_byte_pos = len(out)
        out.append(0)
        flags = 0
        for bit in range(7, -1, -1):
            if i >= size:
                break
            # Search for longest match
            best_len = 0
            best_disp = 0
            search_start = max(0, i - 4096)
            for j in range(search_start, i):
                match_len = 0
                while (match_len < 18 and
                       i + match_len < size and
                       data[j + match_len] == data[i + match_len]):
                    match_len += 1
                    if j + match_len >= i:
                        break
                if match_len >= 3 and match_len > best_len:
                    best_len = match_len
                    best_disp = i - j
            if best_len >= 3:
                flags |= (1 << bit)
                length_field = (best_len - 3) & 0xF
                disp_field = (best_disp - 1) & 0xFFF
                out.append((length_field << 4) | (disp_field >> 8))
                out.append(disp_field & 0xFF)
                i += best_len
            else:
                out.append(data[i])
                i += 1
        out[flag_byte_pos] = flags
    return bytes(out)


def rle_decompress(data: bytes, offset: int = 0) -> bytes:
    """Decompress Nintendo GBA RLE (type 0x30) data."""
    if data[offset] != 0x30:
        raise ValueError(f"Not an RLE block (expected 0x30, got 0x{data[offset]:02X})")
    decompressed_size = data[offset+1] | (data[offset+2] << 8) | (data[offset+3] << 16)
    out = bytearray()
    i = offset + 4
    while len(out) < decompressed_size and i < len(data):
        flag = data[i]; i += 1
        if flag & 0x80:
            count = (flag & 0x7F) + 3
            byte = data[i]; i += 1
            out.extend([byte] * count)
        else:
            count = (flag & 0x7F) + 1
            out.extend(data[i:i + count])
            i += count
    return bytes(out[:decompressed_size])


def load_tbl(tbl_path: str) -> tuple[dict, dict]:
    """Load a .tbl file. Returns (table, reverse_table)."""
    table = {}
    reverse_table = {}
    with open(tbl_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if '=' in line:
                parts = line.split('=', 1)
                if len(parts) == 2:
                    table[parts[0].upper()] = parts[1]
                    reverse_table[parts[1]] = parts[0].upper()
    table['20'] = ' '
    reverse_table[' '] = '20'
    table['0A'] = '\n'
    reverse_table['\n'] = '0A'
    table.pop('00', None)
    return table, reverse_table


def scan_lz77_blocks(rom_data: bytes, min_size: int = 0x10, max_size: int = 0x80000) -> list:
    """Scan ROM for all LZ77-compressed blocks. Returns list of dicts."""
    results = []
    i = 0
    while i < len(rom_data) - 4:
        if rom_data[i] == 0x10:
            dec_size = rom_data[i+1] | (rom_data[i+2] << 8) | (rom_data[i+3] << 16)
            if min_size <= dec_size <= max_size:
                try:
                    decompressed = lz77_decompress(rom_data, i)
                    if len(decompressed) == dec_size:
                        # Estimate compressed size by re-scanning past the block
                        comp_end = _estimate_compressed_end(rom_data, i)
                        results.append({
                            'offset': i,
                            'decompressed_size': dec_size,
                            'compressed_size': comp_end - i,
                            'data': decompressed,
                        })
                        i = comp_end
                        continue
                except Exception:
                    pass
        i += 1
    return results


def huffman_decompress(data: bytes, offset: int = 0, _limit: int = 0) -> bytes:
    """Decompress GBA BIOS Huffman (type 0x24 = 4-bit, 0x28 = 8-bit).

    Header layout (from offset):
      [0]    type byte: 0x24 (4-bit symbols) or 0x28 (8-bit symbols)
      [1-3]  decompressed size, 24-bit little-endian
      [4]    tree_size_byte N — tree table is (N+1)*2 bytes total (including this byte)
      [5..]  tree node bytes (root node first)
      [next 4-byte boundary after tree] bitstream (MSB-first, read 32 bits at a time)

    Tree node format (non-leaf):
      bit 7: left child is a leaf (data) node
      bit 6: right child is a leaf (data) node
      bits 5-0: offset to children pair = (cur_node & ~1) + 2 + 2*offset
    Leaf node: full byte = symbol value (upper nibble unused for 4-bit mode).
    """
    type_byte = data[offset]
    if (type_byte & 0xF0) != 0x20:
        raise ValueError(f"Not Huffman (expected 0x2x, got 0x{type_byte:02X})")
    bits_per_sym = type_byte & 0x0F
    if bits_per_sym not in (4, 8):
        raise ValueError(f"Unsupported Huffman symbol size: {bits_per_sym} (expected 4 or 8)")

    dec_size = data[offset+1] | (data[offset+2] << 8) | (data[offset+3] << 16)
    if dec_size == 0:
        return b''

    tree_size_byte = data[offset + 4]          # N
    tree_table_bytes = (tree_size_byte + 1) * 2  # total incl. size byte
    tree_nodes_start = offset + 5              # root node is first byte here

    # Bitstream starts at next 4-byte boundary after the tree table
    bs_start = offset + ((4 + tree_table_bytes + 3) & ~3)

    out = bytearray()
    bs_pos = bs_start
    bit_buf = 0
    bits_left = 0
    cur_node = 0        # index into tree node array (0 = root)
    pending_nibble = -1  # for 4-bit mode

    def get_bit():
        nonlocal bit_buf, bits_left, bs_pos
        if bits_left == 0:
            bit_buf = (data[bs_pos]
                       | (data[bs_pos + 1] << 8)
                       | (data[bs_pos + 2] << 16)
                       | (data[bs_pos + 3] << 24))
            bs_pos += 4
            bits_left = 32
        b = (bit_buf >> 31) & 1
        bit_buf = (bit_buf << 1) & 0xFFFFFFFF
        bits_left -= 1
        return b

    stop_at = _limit if (_limit > 0 and _limit < dec_size) else dec_size
    max_syms = stop_at * 2 + 64   # guard against infinite loop on bad data
    syms_decoded = 0
    while len(out) < stop_at:
        if syms_decoded > max_syms:
            raise ValueError("Huffman: exceeded symbol limit — bad tree or data")
        syms_decoded += 1
        bit = get_bit()
        node_byte = data[tree_nodes_start + cur_node]
        # Children pair index = round-down-to-even + 2 + 2*(bits 5:0)
        child_pair = (cur_node & ~1) + 2 + 2 * (node_byte & 0x3F)

        if bit == 0:  # left branch
            child = child_pair
            is_leaf = bool(node_byte & 0x80)
        else:          # right branch
            child = child_pair + 1
            is_leaf = bool(node_byte & 0x40)

        if is_leaf:
            sym = data[tree_nodes_start + child]
            if bits_per_sym == 8:
                out.append(sym)
            else:                       # 4-bit: pack two nibbles per byte (lo nibble first)
                if pending_nibble < 0:
                    pending_nibble = sym & 0x0F
                else:
                    out.append(pending_nibble | ((sym & 0x0F) << 4))
                    pending_nibble = -1
            cur_node = 0               # reset to root for next symbol
        else:
            cur_node = child

    return bytes(out[:dec_size])


def scan_huffman_blocks(rom_data: bytes, min_size: int = 0x10, max_size: int = 0x80000,
                        do_4bit: bool = True, do_8bit: bool = True) -> list:
    """Scan ROM for all Huffman-compressed blocks.
    Only checks 4-byte-aligned offsets — GBA BIOS HuffUnComp requires word alignment."""
    results = []
    i = 0
    while i < len(rom_data) - 8:
        b = rom_data[i]
        if (b == 0x24 and do_4bit) or (b == 0x28 and do_8bit):
            dec_size = rom_data[i+1] | (rom_data[i+2] << 8) | (rom_data[i+3] << 16)
            tree_size_byte = rom_data[i + 4]
            if (min_size <= dec_size <= max_size) and (1 <= tree_size_byte <= 127):
                try:
                    # Quick check: decompress only first 256 bytes to verify format
                    quick = huffman_decompress(rom_data, i, _limit=256)
                    if len(quick) == min(dec_size, 256):
                        results.append({
                            'offset': i,
                            'type': 'Huffman-4' if b == 0x24 else 'Huffman-8',
                            'decompressed_size': dec_size,
                        })
                except Exception:
                    pass
        i += 4   # GBA BIOS requires word-aligned input — skip 3 of every 4 bytes
    return results


def scan_rle_blocks(rom_data: bytes, min_size: int = 0x10, max_size: int = 0x80000) -> list:
    """Scan ROM for all RLE-compressed blocks (GBA BIOS type 0x30).
    Only checks 4-byte-aligned offsets — GBA BIOS RLUnComp requires word alignment."""
    results = []
    i = 0
    while i < len(rom_data) - 4:
        if rom_data[i] == 0x30:
            dec_size = rom_data[i+1] | (rom_data[i+2] << 8) | (rom_data[i+3] << 16)
            if min_size <= dec_size <= max_size:
                try:
                    decompressed = rle_decompress(rom_data, i)
                    if len(decompressed) == dec_size:
                        results.append({
                            'offset': i,
                            'type': 'RLE',
                            'decompressed_size': dec_size,
                        })
                except Exception:
                    pass
        i += 4   # word-aligned only
    return results


def _estimate_compressed_end(rom_data: bytes, offset: int) -> int:
    """Walk through an LZ77 block to find where it ends."""
    dec_size = rom_data[offset+1] | (rom_data[offset+2] << 8) | (rom_data[offset+3] << 16)
    out_count = 0
    i = offset + 4
    try:
        while out_count < dec_size and i < len(rom_data):
            flags = rom_data[i]; i += 1
            for bit in range(7, -1, -1):
                if out_count >= dec_size:
                    break
                if (flags >> bit) & 1:
                    i += 2; out_count += ((rom_data[i-2] >> 4) & 0xF) + 3
                else:
                    i += 1; out_count += 1
    except IndexError:
        pass
    return i
