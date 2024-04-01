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

import bittensor as bt
from pydantic import Field

from typing import List


class Commit(bt.Synapse):
    """
    A protocol for handling KZG commitments.
    """

    poly: List[str] = Field(
        ...,
        title="Polynomial",
        description="The polynomial to commit to.",
        allow_mutation=False,
    )
    commitment: str = Field(
        ...,
        title="Commitment",
        description="The commitment to the polynomial.",
        allow_mutation=True,
    )


class Open(bt.Synapse):
    """
    A protocol for proving KZG commitments.
    """

    commitment: str = Field(
        ...,
        title="Commitment",
        description="The commitment to prove.",
        allow_mutation=False,
    )
    x: str = Field(
        ...,
        title="Input",
        description="The input to evaluate the polynomial at.",
        allow_mutation=False,
    )

    proof: str = Field(
        ...,
        title="Proof",
        description="The proof of the commitment.",
        allow_mutation=True,
    )


class Verify(bt.Synapse):
    """
    A protocol for verifying KZG commitments.
    """

    commitment: str = Field(
        ..., title="Commitment", description="The commitment to verify."
    )
    y: str = Field(
        ...,
        title="Output",
        description="The output of the polynomial at x.",
        allow_mutation=False,
    )
    x: str = Field(
        ...,
        title="Input",
        description="The input to evaluate the polynomial at.",
        allow_mutation=False,
    )
    proof: str = Field(
        ...,
        title="Proof",
        description="The proof of the commitment.",
        allow_mutation=False,
    )

    valid: bool = Field(
        ...,
        title="Valid",
        description="Whether the proof is valid.",
        allow_mutation=False,
    )
