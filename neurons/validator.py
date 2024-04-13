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

# Import forward dependencies.
from base.protocol import Prove
# import base validator class which takes care of most of the boilerplate
from base.validator import BaseValidatorNeuron
from utils.uids import get_random_uids


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

    def rpc_random_poly(self, degree: int) -> str:
        with self.client.random_poly(degree) as response:
            if response.status_code != 200:
                bt.logging.error(
                    f"RPC request failed with status: {response.status_code}"
                )
                raise Exception("Failed to generate a random polynomial.")
            return response.json().get("result", {}).get("poly")

    def rpc_verify(self, proof: str, x: str, y: str, commitment: str) -> bool:
        with self.client.verify(proof, x, y, commitment) as response:
            if response.status_code != 200:
                bt.logging.error(
                    f"RPC request failed with status: {response.status_code}"
                )
                raise Exception("Failed to verify the proof.")
            return response.json().get("result", {}).get("valid")

    def rpc_random_x(self) -> str:
        with self.client.random_point() as response:
            if response.status_code != 200:
                bt.logging.error(
                    f"RPC request failed with status: {response.status_code}"
                )
                raise Exception("Failed to generate a random x.")
            return response.json().get("result", {}).get("point")

    def rpc_eval(self, poly: str, x: str) -> str:
        with self.client.eval(poly, x) as response:
            if response.status_code != 200:
                bt.logging.error(
                    f"RPC request failed with status: {response.status_code}"
                )
                raise Exception("Failed to evaluate the polynomial.")
            return response.json().get("result", {}).get("y")

    def generate_challenge(self, degree: int=(2**20) - 1) -> Prove:
        """
        Generate a challenge for the miners to solve.
        """

        # Generate a random polynomial.
        poly = self.rpc_random_poly(degree)
        x = self.rpc_random_x()
        y = self.rpc_eval(poly, x)
        return Prove(poly=poly, x=x, y=y)

    async def forward(self):
        try:
            bt.logging.info("generating challenge for miners")
            challenge = self.generate_challenge()
            bt.logging.info("sending challenge to miners")
            await self.query(challenge)
        except Exception as e:
            bt.logging.error(f"Failed to generate a query challenge: {e}")
            bt.logging.error("Retrying in 5 seconds...")

    def reward(
        self,
        challenge: Prove,
        response: Prove,
        response_process_time: float,
        min_process_time: float,
        timeout: float,
    ) -> float:
        """
        Calculate the miner reward based on correctness and processing time.
        """

        # Don't bother verifying if we don't have all info
        if (
            response.commitment is None
            or response.proof is None
        ):
            bt.logging.warning("Received incomplete proof.")
            return 0.0

        # Don't even bother spending resources on verifying if the synapse came in too late
        if response_process_time > timeout:
            bt.logging.warning("Received proof which was too slow.")
            return 0.0

        valid = self.rpc_verify(
            proof=response.proof,
            x=challenge.x,
            y=challenge.y,
            commitment=response.commitment,
        )

        if not valid:
            bt.logging.warning("Invalid proof.")
            return 0.0

        time_off_from_min = response_process_time - min_process_time
        max_time = timeout - min_process_time
        return 1.0 - time_off_from_min / max_time

    def get_rewards(
        self,
        challenge: Prove,
        responses: List[Tuple[Prove, float]],
        timeout: float,
    ) -> torch.FloatTensor:
        """
        Calculate the miner rewards based on correctness and processing time.
        """
        # Get the fastest processing time.
        min_process_time = min([response[1] for response in responses])
        return torch.FloatTensor(
            [
                self.reward(challenge, response[0], response[1], min_process_time, timeout)
                for response in responses
            ]
        ).to(self.device)

    async def query(self, challenge: Prove) -> torch.FloatTensor:
        """
        Query the connected miners with a challenge
        """
        miner_uids = get_random_uids(
            self, k=min(self.config.neuron.sample_size, self.metagraph.n.item())
        )
        timeout = 60
        responses = await self.dendrite(
            axons=[self.metagraph.axons[uid] for uid in miner_uids],
            synapse=challenge,
            deserialize=False,  # bogus responses shouldn't kill the validation flow
            timeout=timeout,
        )

        # Empty responses shouldn't be used for min_process_time.
        for resp in responses:
            if (
                resp.commitment is None
                or resp.proof is None
            ):
                resp.dendrite.process_time = timeout + 1.0

        responses = [(resp, resp.dendrite.process_time) for resp in responses]

        # Adjust the scores based on responses from miners.
        rewards = self.get_rewards(challenge, responses, timeout)
        bt.logging.info(f"Scored responses: {rewards}")

        # Update the scores based on the rewards. You may want to define your own update_scores function for custom behavior.
        self.update_scores(rewards, miner_uids)


# The main function parses the configuration and runs the validator.
if __name__ == "__main__":
    with Validator() as validator:
        while True:
            bt.logging.info("Validator running...", time.time())
            time.sleep(5)
