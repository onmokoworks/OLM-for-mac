"""
cv_bridge.py — IplImage <-> numpy bridge for the .aex OpenCV detour layer.

Per OPENCV_DETOUR_DESIGN.md rev 2 §4: the objects passed to the DistanceGradation
OpenCV entry points (cvThreshold FUN_1812b6a40, cvDistTransform FUN_1812b15a0,
cvResize FUN_1812aef70, ...) are **IplImage** pointers (OpenCV C API), NOT cv::Mat.
IplImage is a frozen public C ABI, so we decode it by fixed x64 offsets rather than
the sentinel-pinning ceremony rev 1 planned for cv::Mat.

x64 IplImage layout (sizeof == 0x90; this is also the value the binary's cvGetSize
gate checks, FUN_1811765a0 `*param_1 == 0x90`):

    0x00 int    nSize          (== 0x90 for a valid IplImage header)
    0x04 int    ID
    0x08 int    nChannels
    0x0c int    alphaChannel
    0x10 int    depth          (IPL_DEPTH_*; sign bit 0x80000000 for signed)
    0x14 char   colorModel[4]
    0x18 char   channelSeq[4]
    0x1c int    dataOrder
    0x20 int    origin
    0x24 int    align
    0x28 int    width
    0x2c int    height
    0x30 void*  roi
    0x38 void*  maskROI
    0x40 void*  imageId
    0x48 void*  tileInfo
    0x50 int    imageSize
    0x58 char*  imageData
    0x60 int    widthStep
    0x64 int    BorderMode[4]
    0x74 int    BorderConst[4]
    0x88 char*  imageDataOrigin

This module only depends on numpy (already in the venv) and the AexLoader's
read_bytes/write_bytes/bump_alloc. No cv2 dependency (see design §5: P0/P1 are
cv2-free).
"""

from __future__ import annotations

import struct
from typing import Optional

import numpy as np

# -- IplImage field offsets (x64) -------------------------------------------
IPL_SIZE            = 0x90   # sizeof(IplImage) on x64; the nSize sentinel value
OFF_NSIZE           = 0x00
OFF_ID              = 0x04
OFF_NCHANNELS       = 0x08
OFF_ALPHACHANNEL    = 0x0C
OFF_DEPTH           = 0x10
OFF_DATAORDER       = 0x1C
OFF_ORIGIN          = 0x20
OFF_ALIGN           = 0x24
OFF_WIDTH           = 0x28
OFF_HEIGHT          = 0x2C
OFF_ROI             = 0x30
OFF_MASKROI         = 0x38
OFF_IMAGEID         = 0x40
OFF_TILEINFO        = 0x48
OFF_IMAGESIZE       = 0x50
OFF_IMAGEDATA       = 0x58
OFF_WIDTHSTEP       = 0x60
OFF_IMAGEDATAORIGIN = 0x88

# -- IPL depth codes ---------------------------------------------------------
IPL_DEPTH_SIGN = 0x80000000
IPL_DEPTH_1U   = 1
IPL_DEPTH_8U   = 8
IPL_DEPTH_16U  = 16
IPL_DEPTH_32F  = 32
IPL_DEPTH_8S   = (IPL_DEPTH_SIGN | 8)
IPL_DEPTH_16S  = (IPL_DEPTH_SIGN | 16)
IPL_DEPTH_32S  = (IPL_DEPTH_SIGN | 32)
IPL_DEPTH_64F  = 64

# depth code -> (numpy dtype, itemsize bytes)
_DEPTH_TO_DTYPE = {
    IPL_DEPTH_8U:  (np.uint8,   1),
    IPL_DEPTH_16U: (np.uint16,  2),
    IPL_DEPTH_32F: (np.float32, 4),
    IPL_DEPTH_8S:  (np.int8,    1),
    IPL_DEPTH_16S: (np.int16,   2),
    IPL_DEPTH_32S: (np.int32,   4),
    IPL_DEPTH_64F: (np.float64, 8),
}
_DTYPE_TO_DEPTH = {
    np.dtype(np.uint8):   IPL_DEPTH_8U,
    np.dtype(np.uint16):  IPL_DEPTH_16U,
    np.dtype(np.float32): IPL_DEPTH_32F,
    np.dtype(np.int8):    IPL_DEPTH_8S,
    np.dtype(np.int16):   IPL_DEPTH_16S,
    np.dtype(np.int32):   IPL_DEPTH_32S,
    np.dtype(np.float64): IPL_DEPTH_64F,
}


class IplHeader:
    """Decoded fields of a guest IplImage plus its guest pointer."""

    __slots__ = ("ptr", "nSize", "nChannels", "depth", "width", "height",
                 "imageSize", "imageData", "widthStep", "imageDataOrigin")

    def __init__(self, ptr, nSize, nChannels, depth, width, height,
                 imageSize, imageData, widthStep, imageDataOrigin):
        self.ptr = ptr
        self.nSize = nSize
        self.nChannels = nChannels
        self.depth = depth
        self.width = width
        self.height = height
        self.imageSize = imageSize
        self.imageData = imageData
        self.widthStep = widthStep
        self.imageDataOrigin = imageDataOrigin

    def dtype_info(self):
        if self.depth not in _DEPTH_TO_DTYPE:
            raise ValueError(f"unsupported IPL depth 0x{self.depth & 0xFFFFFFFF:x}")
        return _DEPTH_TO_DTYPE[self.depth]

    def __repr__(self):
        return (f"IplHeader(ptr=0x{self.ptr:x}, {self.width}x{self.height}x{self.nChannels}, "
                f"depth=0x{self.depth & 0xFFFFFFFF:x}, step={self.widthStep}, "
                f"data=0x{self.imageData:x})")


def _rd_i32(loader, addr):
    return struct.unpack("<i", loader.read_bytes(addr, 4))[0]


def _rd_u32(loader, addr):
    return struct.unpack("<I", loader.read_bytes(addr, 4))[0]


def _rd_ptr(loader, addr):
    return struct.unpack("<Q", loader.read_bytes(addr, 8))[0]


def read_header(loader, ipl_ptr) -> IplHeader:
    """Decode a guest IplImage header at ipl_ptr into an IplHeader."""
    nSize = _rd_i32(loader, ipl_ptr + OFF_NSIZE)
    return IplHeader(
        ptr=ipl_ptr,
        nSize=nSize,
        nChannels=_rd_i32(loader, ipl_ptr + OFF_NCHANNELS),
        depth=_rd_u32(loader, ipl_ptr + OFF_DEPTH),
        width=_rd_i32(loader, ipl_ptr + OFF_WIDTH),
        height=_rd_i32(loader, ipl_ptr + OFF_HEIGHT),
        imageSize=_rd_i32(loader, ipl_ptr + OFF_IMAGESIZE),
        imageData=_rd_ptr(loader, ipl_ptr + OFF_IMAGEDATA),
        widthStep=_rd_i32(loader, ipl_ptr + OFF_WIDTHSTEP),
        imageDataOrigin=_rd_ptr(loader, ipl_ptr + OFF_IMAGEDATAORIGIN),
    )


def read_ipl(loader, ipl_ptr) -> np.ndarray:
    """
    Read a guest IplImage into a numpy array of shape (h, w) for 1 channel or
    (h, w, c) for c>1, honoring widthStep (row stride may exceed w*c*itemsize).
    Returns a COPY (not a view over guest memory).
    """
    hdr = read_header(loader, ipl_ptr)
    dtype, itemsize = hdr.dtype_info()
    if hdr.nSize != IPL_SIZE:
        raise ValueError(f"nSize=0x{hdr.nSize:x} != 0x{IPL_SIZE:x}; not a valid IplImage at 0x{ipl_ptr:x}")
    row_bytes = hdr.width * hdr.nChannels * itemsize
    out = np.empty((hdr.height, hdr.width * hdr.nChannels), dtype=dtype)
    for y in range(hdr.height):
        raw = loader.read_bytes(hdr.imageData + y * hdr.widthStep, row_bytes)
        out[y] = np.frombuffer(raw, dtype=dtype, count=hdr.width * hdr.nChannels)
    if hdr.nChannels > 1:
        return out.reshape(hdr.height, hdr.width, hdr.nChannels)
    return out


def write_ipl(loader, ipl_ptr, arr: np.ndarray) -> None:
    """
    Write a numpy array back into a guest IplImage's existing imageData buffer,
    honoring widthStep. Shape/dtype must match the destination header.
    """
    hdr = read_header(loader, ipl_ptr)
    dtype, itemsize = hdr.dtype_info()
    a = np.ascontiguousarray(arr, dtype=dtype)
    flat = a.reshape(hdr.height, hdr.width * hdr.nChannels)
    row_bytes = hdr.width * hdr.nChannels * itemsize
    for y in range(hdr.height):
        loader.write_bytes(hdr.imageData + y * hdr.widthStep, flat[y].tobytes()[:row_bytes])


def build_ipl(loader, arr: np.ndarray, *, align_step: int = 4) -> int:
    """
    Allocate a guest IplImage header (0x90 bytes) + a data buffer via
    loader.bump_alloc, populate the header from `arr`, and return the header
    pointer. Row stride = ceil(w*c*itemsize / align_step) * align_step.

    This lets a test construct a valid IplImage the binary's cvarrToMat accepts
    without driving the PF Handle Suite path (design §4).
    """
    arr = np.asarray(arr)
    if arr.ndim == 2:
        h, w = arr.shape
        c = 1
    elif arr.ndim == 3:
        h, w, c = arr.shape
    else:
        raise ValueError("arr must be 2-D (h,w) or 3-D (h,w,c)")
    dt = np.dtype(arr.dtype)
    if dt not in _DTYPE_TO_DEPTH:
        raise ValueError(f"unsupported numpy dtype {dt}")
    depth = _DTYPE_TO_DEPTH[dt]
    itemsize = dt.itemsize
    row_bytes = w * c * itemsize
    step = ((row_bytes + align_step - 1) // align_step) * align_step
    image_size = step * h

    data_ptr = loader.bump_alloc(image_size, align=16)
    hdr_ptr = loader.bump_alloc(IPL_SIZE, align=16)

    # zero the header, then fill fields
    loader.write_bytes(hdr_ptr, b"\x00" * IPL_SIZE)
    loader.write_bytes(hdr_ptr + OFF_NSIZE,     struct.pack("<i", IPL_SIZE))
    loader.write_bytes(hdr_ptr + OFF_ID,        struct.pack("<i", 0))
    loader.write_bytes(hdr_ptr + OFF_NCHANNELS, struct.pack("<i", c))
    loader.write_bytes(hdr_ptr + OFF_DEPTH,     struct.pack("<I", depth & 0xFFFFFFFF))
    loader.write_bytes(hdr_ptr + OFF_DATAORDER, struct.pack("<i", 0))   # interleaved
    loader.write_bytes(hdr_ptr + OFF_ORIGIN,    struct.pack("<i", 0))   # top-left
    loader.write_bytes(hdr_ptr + OFF_ALIGN,     struct.pack("<i", align_step))
    loader.write_bytes(hdr_ptr + OFF_WIDTH,     struct.pack("<i", w))
    loader.write_bytes(hdr_ptr + OFF_HEIGHT,    struct.pack("<i", h))
    loader.write_bytes(hdr_ptr + OFF_IMAGESIZE, struct.pack("<i", image_size))
    loader.write_bytes(hdr_ptr + OFF_IMAGEDATA, struct.pack("<Q", data_ptr))
    loader.write_bytes(hdr_ptr + OFF_WIDTHSTEP, struct.pack("<i", step))
    loader.write_bytes(hdr_ptr + OFF_IMAGEDATAORIGIN, struct.pack("<Q", data_ptr))

    # fill the data buffer (zero padding beyond row_bytes)
    loader.write_bytes(data_ptr, b"\x00" * image_size)
    write_ipl(loader, hdr_ptr, arr)
    return hdr_ptr


def read_stack_arg(loader, n: int) -> int:
    """
    Read the n-th (0-based) integer argument from the stack at the moment a
    detour handler runs. Args 0-3 are in RCX/RDX/R8/R9 (use loader args);
    args >= 4 live on the caller's stack.

    At the detour stub, RSP still points at the caller's return address (the
    12-byte `mov rax,imm; jmp rax` patch pushes nothing), so:
        arg4 is at [RSP + 8 (retaddr) + 0x20 (shadow)]  = [RSP + 0x28]
        argN is at [RSP + 0x28 + (N-4)*8]
    (design §6).
    """
    if n < 4:
        raise ValueError("use RCX/RDX/R8/R9 for args 0-3")
    from unicorn.x86_const import UC_X86_REG_RSP
    rsp = loader.uc.reg_read(UC_X86_REG_RSP)
    addr = rsp + 0x28 + (n - 4) * 8
    return _rd_ptr(loader, addr)
