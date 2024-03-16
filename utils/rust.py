# The MIT License (MIT)
# Copyright © 2024 Apollo

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import ctypes
from os import path
from typing import Tuple

here = path.abspath(path.dirname(__file__))
head_tail = path.split(here)
LIB_PATH = path.join(head_tail[0], "prover")

class ByteData(ctypes.Structure):
    _fields_ = [("data", ctypes.POINTER(ctypes.c_ubyte)),
                ("len", ctypes.c_size_t)]

class DoubleByteData(ctypes.Structure):
    _fields_ = [("first", ByteData),
                ("second", ByteData)]

def make_proof(main_trace: bytes, pub_inputs: bytes) -> bytes:
    prover = ctypes.CDLL(LIB_PATH)
    prover.generate_proof_from_trace.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t,ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t]
    prover.generate_proof_from_trace.restype = ctypes.POINTER(ByteData)

    prover.free_byte_data.argtypes = [ctypes.POINTER(ByteData)]

    trace_bytes = (ctypes.c_ubyte * len(main_trace))(*main_trace)
    memory_bytes = (ctypes.c_ubyte * len(pub_inputs))(*pub_inputs)
    byte_data = prover.generate_proof_from_trace(trace_bytes, len(main_trace), memory_bytes, len(pub_inputs))

    proof_bytes = bytes(byte_data.contents.data[:byte_data.contents.len])

    # Give ownership of the memory back to rust so that it can be safely erased
    prover.free_byte_data(byte_data)

    return proof_bytes

def make_trace_and_pub_inputs(program: str) -> Tuple[bytes, bytes]:
    # Compile Cairo program and retrieve execution trace and public inputs.
    prover = ctypes.CDLL(LIB_PATH)
    prover.generate_trace_and_inputs.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t]
    prover.generate_trace_and_inputs.restype = ctypes.POINTER(DoubleByteData)

    prover.free_double_byte_data.argtypes = [ctypes.POINTER(DoubleByteData)]

    program = program.encode()
    program_bytes = (ctypes.c_ubyte * len(program))(*program)
    double_bytes = prover.generate_trace_and_inputs(program_bytes, len(program))

    main_trace_bytes = bytes(double_bytes.contents.first.data[:double_bytes.contents.first.len])
    pub_inputs_bytes = bytes(double_bytes.contents.second.data[:double_bytes.contents.second.len])

    # Give ownership of the memory back to rust so that it can be safely erased
    prover.free_double_byte_data(double_bytes)

    return main_trace_bytes, pub_inputs_bytes
