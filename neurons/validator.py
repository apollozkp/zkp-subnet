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
from typing import List, Tuple

# Bittensor
import bittensor as bt
import torch
from fourier import Client

# Import forward dependencies.
from base.protocol import Commit, Open, Verify

# import base validator class which takes care of most of the boilerplate
from base.validator import BaseValidatorNeuron
from utils.uids import get_random_uids

class Challenge:
    def __init__(self, poly: str, x: str, y: str, commitment: str, proof: str):
        self.poly = poly
        self.x = x
        self.y = y
        self.commitment = commitment

    def synapse(self):
        return Open(
            poly=self.poly,
            x=self.x,
        )

class Validator(BaseValidatorNeuron):
    """
    Validator class for the ZKG network.
    The validator handles the following tasks:
    - challenge: Generate a challenge for the miners to solve.
    - verify: Verifies proofs generated on challenges by miners.
    """

    def __init__(self, config=None):
        super(Validator, self).__init__(config=config)
        bt.logging.info("load_state()")
        self.load_state()
        # change port to 1338 so it doesn't conflict with the miner
        PORT = 1338
        self.client = Client(port=PORT)
        self.client.start()

    def rpc_verify(self, proof: str, x: str, y: str, commitment: str) -> bool:
        with self.client.verify(proof, x, y, commitment) as response:
            if response.status_code != 200:
                bt.logging.error(
                    f"RPC request failed with status: {response.status_code}"
                )
                raise Exception("Failed to verify the proof.")
            return response.json().get("result", {}).get("valid")

    async def generate_challenge(self) -> Prove:
        """
        Generate a challenge for the miners to solve.
        """

        # Generate a random polynomial.
        DEGREE = 10
        poly = self.rpc_random_poly(DEGREE)
        return Prove(poly)

    async def forward(self):
        bt.logging.debug("Sleeping for 5 seconds...")
        time.sleep(5)
        try:
            challenge = await self.generate_challenge()
            await self.query(challenge)
        except Exception as e:
            bt.logging.error(f"Failed to generate and query challenge: {e}")
            bt.logging.error("Retrying in 5 seconds...")

    def reward(self, response: Prove, response_process_time: float, min_process_times: float, timeout: float) -> float:
        """
        Calculate the miner reward based on correctness and processing time.
        """

        # Don't bother verifying if we don't have all info
        if response.commitment is None or response.y is None or response.x is None or response.proof is None:
            bt.logging.warn("Received incomplete proof.")
            return 0.0

        # Don't even bother spending resources on verifying if the synapse came in too late
        if response_process_time > timeout:
            bt.logging.warn("Received proof which was too slow.")
            return 0.0

        valid = self.rpc_verify(
            proof=response.proof,
            x=response.x,
            y=response.y,
            commitment=response.commitment,
        )

        if not valid:
            bt.logging.warn("Invalid proof.")
            return 0.0

        time_off_from_min = response_process_time - min_process_time
        max_time = timeout - min_process_time
        return 1.0 - time_off_from_min / max_time

    def get_rewards(
        self,
        challenge: Verify,
        responses: List[Open],
        timeout: float,
    ) -> torch.FloatTensor:
        """
        Calculate the miner rewards based on correctness and processing time.
        """
        # How to get the processing time?
        return torch.FloatTensor(
            [self.reward(challenge, response, timeout) for response in responses]
        ).to(self.device)

    async def query(self, challenge: Challenge) -> torch.FloatTensor:
        """
        Query the connected miners with a challenge
        """
        miner_uids = get_random_uids(
            self, k=min(self.config.neuron.sample_size, self.metagraph.n.item())
        )
        timeout = 10
        responses = await self.dendrite(
            axons=[self.metagraph.axons[uid] for uid in miner_uids],
            synapse=self.generate_challenge(),
            deserialize=False,  # bogus responses shouldn't kill the validation flow
            timeout=timeout,
        )

        # Adjust the scores based on responses from miners.
        rewards = self.get_rewards(challenge.truth(), responses, timeout)
        bt.logging.info(f"Scored responses: {rewards}")

        # Update the scores based on the rewards. You may want to define your own update_scores function for custom behavior.
        self.update_scores(rewards, miner_uids)


# The main function parses the configuration and runs the validator.
if __name__ == "__main__":
    with Validator() as validator:
        while True:
            bt.logging.info("Validator running...", time.time())
            time.sleep(5)
