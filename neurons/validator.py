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


import time
import torch
from typing import List

# Bittensor
import bittensor as bt

# import base validator class which takes care of most of the boilerplate
from base.validator import BaseValidatorNeuron

# Import forward dependencies.
from base.protocol import Trace
from utils.cairo_generator import generate_random_cairo_trace
from utils.uids import get_random_uids

class Validator(BaseValidatorNeuron):
    def __init__(self, config=None):
        super(Validator, self).__init__(config=config)
        bt.logging.info("load_state()")
        self.load_state()

    async def forward(self):
        miner_uids = get_random_uids(self, k=min(self.config.neuron.sample_size, self.metagraph.n.item()))
        trace, proof_bytes = generate_random_cairo_trace()

        # For completeness, validators also need to generate proofs to ensure that miners are generating
        # proofs of the given trace, rather than just creating any random garbage proof that will pass
        # verification.

        responses = await self.dendrite(
            axons=[self.metagraph.axons[uid] for uid in miner_uids],
            synapse=trace, # send in the execution trace
            deserialize=False, # bogus responses shouldn't kill the validation flow
            timeout=10,
        )

        def try_deserialize(item: Trace):
            try:
                return item.deserialize()
            except:
                return bytes()

        responses = [try_deserialize(item) for item in responses]

        # Log the results for monitoring purposes. We don't log the actual response since
        # proofs are enormous and it would pollute the logs.
        bt.logging.info(f"Received responses.")

        # Adjust the scores based on responses from miners.
        rewards = self.get_rewards(proof_bytes, responses)

        bt.logging.info(f"Scored responses: {rewards}")
        # Update the scores based on the rewards. You may want to define your own update_scores function for custom behavior.
        self.update_scores(rewards, miner_uids)

    def get_rewards(
        self,
        proof_bytes: bytes,
        responses: List[bytes],
    ) -> torch.FloatTensor:
        return torch.FloatTensor(
            [reward(proof_bytes, response_proof) for response_proof in responses]
        ).to(self.device)

# it's sufficient for us to check exact matches between proof bytes and pub inputs bytes.
# verifying the proof would be redundant at this stage, but a later update would likely make
# it more sensible to opt for proof verification instead of byte matching
def reward(proof_bytes: bytes, response_proof: bytes) -> float:
    if proof_bytes != response_proof:
        return 0.0

    return 1.0


# The main function parses the configuration and runs the validator.
if __name__ == "__main__":
    with Validator() as validator:
        while True:
            bt.logging.info("Validator running...", time.time())
            time.sleep(5)
