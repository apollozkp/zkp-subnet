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
from typing import List, Tuple

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
        # For completeness, validators also need to generate proofs to ensure that miners are generating
        # proofs of the given trace, rather than just creating any random garbage proof that will pass
        # verification.
        trace, proof_bytes = generate_random_cairo_trace()
        await query(self, trace, proof_bytes)

    def get_rewards(
        self,
        proof_bytes: bytes,
        responses: List[Tuple[bytes, float]],
        timeout: float,
    ) -> torch.FloatTensor:
        # Get the fastest processing time.
        min_process_time = min([response[1] for response in responses])
        return torch.FloatTensor(
            [reward(proof_bytes, response[0], response[1], min_process_time, timeout) for response in responses]
        ).to(self.device)

async def query(self, trace: Trace, proof_bytes: bytes) -> torch.FloatTensor:
    miner_uids = get_random_uids(self, k=min(self.config.neuron.sample_size, self.metagraph.n.item()))
    timeout = 10
    responses = await self.dendrite(
        axons=[self.metagraph.axons[uid] for uid in miner_uids],
        synapse=trace, # send in the execution trace
        deserialize=False, # bogus responses shouldn't kill the validation flow
        timeout=timeout,
    )

    def try_deserialize(item: Trace):
        try:
            return item.deserialize(), item.dendrite.process_time
        except:
            return bytes(), timeout + 1.0

    responses = [try_deserialize(item) for item in responses]

    # Log the results for monitoring purposes. We don't log the actual response since
    # proofs are enormous and it would pollute the logs.
    bt.logging.info(f"Received responses.")

    # Adjust the scores based on responses from miners.
    rewards = self.get_rewards(proof_bytes, responses, timeout)
    bt.logging.info(f"Scored responses: {rewards}")

    # Update the scores based on the rewards. You may want to define your own update_scores function for custom behavior.
    self.update_scores(rewards, miner_uids)

# it's sufficient for us to check exact matches between proof bytes and pub inputs bytes.
# verifying the proof would be redundant at this stage, but a later update would likely make
# it more sensible to opt for proof verification instead of byte matching
def reward(proof_bytes: bytes, response_proof: bytes, response_process_time: float, min_process_time: float, timeout: float) -> float:
    if response_process_time > timeout:
        return 0.0

    if proof_bytes != response_proof:
        return 0.0

    time_off_from_min = response_process_time - min_process_time
    max_time = timeout - min_process_time
    return 1.0 - time_off_from_min / max_time

# The main function parses the configuration and runs the validator.
if __name__ == "__main__":
    with Validator() as validator:
        while True:
            bt.logging.info("Validator running...", time.time())
            time.sleep(5)
