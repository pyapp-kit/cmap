import io
import struct
import zlib

import numpy as np

o32 = struct.Struct(">I")


def encode_png(ary: np.ndarray) -> bytes:
    try:
        from PIL import Image
    except ImportError:
        return _encode_png(ary)
    else:
        with io.BytesIO() as fp:
            Image.fromarray(ary).save(fp, format="png")
            return fp.getvalue()


def _encode_png(image_data: np.ndarray) -> bytes:
    """Super basic PNG encoder. Only supports 3-channel RGB images."""
    # Check image data dimensions
    if image_data.ndim != 3:
        raise ValueError("Image data must be a 3D numpy array")
    if image_data.shape[2] == 4:
        # throwing away alpha channel
        image_data = image_data[:, :, :3]
    if image_data.shape[2] != 3:
        raise ValueError("Image data must be RGB or RGBA")

    image_data = image_data.astype(">u1")
    height, width = image_data.shape[:2]

    # PNG header
    png_bytes = b"\x89PNG\r\n\x1a\n"

    # IHDR chunk
    png_bytes += _makechunk(
        b"IHDR",
        o32.pack(width),  # 0: size
        o32.pack(height),
        b"\x08\x02",  # 8: RGB mode
        b"\0",  # 10: compression
        b"\0",  # 11: filter category
        b"\0",  # 12: interlace flag
    )

    # IDAT chunk
    scanlines = b"".join(b"\x00" + row.tobytes() for row in image_data)
    png_bytes += _makechunk(b"IDAT", zlib.compress(scanlines))

    # IEND chunk
    png_bytes += _makechunk(b"IEND", b"")
    return png_bytes


def _crc32(data: bytes, seed: int = 0) -> int:
    return zlib.crc32(data, seed) & 0xFFFFFFFF


def _makechunk(cid: bytes, *data: bytes) -> bytes:
    """Write a PNG chunk (including CRC field)."""
    _data = b"".join(data)
    out = o32.pack(len(_data)) + cid + _data
    crc = _crc32(_data, _crc32(cid))
    return out + o32.pack(crc)
