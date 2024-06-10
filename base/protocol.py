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

from typing import List, Optional

import bittensor as bt
from pydantic import Field


class Prove(bt.Synapse):
    """
    A protocol for proving KZG commitments.
    """

    index: int = Field(
        ...,
        title="Worker Index",
        description="The Index that the miner should use to identify itself.",
        frozen=True,
    )
    poly: List[str] = Field(
        ...,
        title="Polynomial",
        description="The polynomial to prove.",
        frozen=True,
    )
    alpha: Optional[str] = Field(
        title="Input",
        description="The input to evaluate the polynomial at.",
        default=None,
    )
    eval: Optional[str] = Field(
        title="Evaluation",
        description="The evaluation of the polynomial at the input.",
        default=None,
    )
    commitment: Optional[str] = Field(
        title="Commitment",
        description="The commitment to the polynomial.",
        default=None,
    )
    proof: Optional[str] = Field(
        title="Proof",
        description="The proof of the commitment.",
        default=None,
    )

    def deserialize(self):
        return self
