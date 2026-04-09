"""
Secure Memory Utilities — Ensures cryptographic material and decrypted data
are properly wiped from RAM after use.
"""
from __future__ import annotations

import ctypes
import gc
import io
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


def secure_wipe_bytes(data: bytearray | bytes) -> None:
    """
    Overwrite memory contents with zeros using ctypes.memset.
    Works on mutable bytearray. For bytes objects, we attempt best-effort.
    """
    if isinstance(data, bytearray):
        ctypes.memset(
            (ctypes.c_char * len(data)).from_buffer(data),
            0,
            len(data)
        )
    elif isinstance(data, bytes) and len(data) > 0:
        # bytes are immutable, but we can try to overwrite the buffer
        try:
            buf = (ctypes.c_char * len(data)).from_address(id(data) + bytes.__basicsize__ - 1)
            ctypes.memset(buf, 0, len(data))
        except Exception:
            pass  # Immutable — can't guarantee wipe, rely on GC


def secure_wipe_buffer(buffer: io.BytesIO) -> None:
    """
    Securely wipe the contents of a BytesIO buffer.
    Overwrites internal buffer with zeros, then truncates.
    """
    if buffer is None:
        return
    try:
        content = buffer.getvalue()
        size = len(content)
        
        # Overwrite buffer contents
        buffer.seek(0)
        buffer.write(b'\x00' * size)
        buffer.truncate(size)
        buffer.seek(0)
        
        # Also try to wipe the original content bytes
        if isinstance(content, bytes) and size > 0:
            try:
                buf_addr = id(content) + bytes.__basicsize__ - 1
                buf = (ctypes.c_char * size).from_address(buf_addr)
                ctypes.memset(buf, 0, size)
            except Exception:
                pass
        
        # Close and discard
        buffer.close()
        del content
        gc.collect()
        
        logger.debug(f"Securely wiped {size} bytes from memory buffer")
    except Exception as e:
        logger.warning(f"Memory wipe encountered issue: {e}")
        try:
            buffer.close()
        except Exception:
            pass


def secure_wipe_tensor(tensor) -> None:
    """
    Zero out a PyTorch tensor's data in-place and delete it.
    """
    try:
        if tensor is not None and hasattr(tensor, 'zero_'):
            tensor.zero_()
            del tensor
    except Exception as e:
        logger.warning(f"Tensor wipe issue: {e}")


@contextmanager
def SecureBuffer():
    """
    Context manager that provides a BytesIO buffer and securely wipes it on exit.
    
    Usage:
        with SecureBuffer() as buf:
            buf.write(sensitive_data)
            # Use data...
        # Buffer is securely wiped here
    """
    buffer = io.BytesIO()
    try:
        yield buffer
    finally:
        secure_wipe_buffer(buffer)


@contextmanager
def SecureDataScope():
    """
    Context manager that tracks all BytesIO buffers and tensors created
    within its scope and wipes them on exit.
    
    Usage:
        with SecureDataScope() as scope:
            buf = scope.track_buffer(some_buffer)
            tensor = scope.track_tensor(some_tensor)
        # Everything wiped
    """
    scope = _SecureScope()
    try:
        yield scope
    finally:
        scope.wipe_all()


class _SecureScope:
    """Internal tracker for secure data cleanup."""
    
    def __init__(self):
        self._buffers: list[io.BytesIO] = []
        self._tensors: list = []
    
    def track_buffer(self, buf: io.BytesIO) -> io.BytesIO:
        self._buffers.append(buf)
        return buf
    
    def track_tensor(self, tensor):
        self._tensors.append(tensor)
        return tensor
    
    def wipe_all(self):
        for buf in self._buffers:
            secure_wipe_buffer(buf)
        for tensor in self._tensors:
            secure_wipe_tensor(tensor)
        self._buffers.clear()
        self._tensors.clear()
        gc.collect()
        logger.info("SecureDataScope: All tracked data wiped")
