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

import torch
from typing import List

# it's sufficient for us to check exact matches between proof bytes and pub inputs bytes.
# verifying the proof would be redundant at this stage, but a later update would likely make
# it more sensible to opt for proof verification instead of byte matching
def reward(proof_bytes: bytes, response_proof: bytes) -> float:
    if proof_bytes != response_proof:
        return 0.0

    return 1.0


def get_rewards(
    self,
    proof_bytes: bytes,
    responses: List[bytes],
) -> torch.FloatTensor:
    return torch.FloatTensor(
        [reward(proof_bytes, response_proof) for response_proof in responses]
    ).to(self.device)
