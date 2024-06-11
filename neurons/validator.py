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


import asyncio
import time
from typing import List

# Bittensor
import bittensor as bt
import numpy as np

# Import forward dependencies.
from base.protocol import Prove

# import base validator class which takes care of most of the boilerplate
from base.validator import BaseValidatorNeuron
from utils.uids import get_random_uids


class Challenge:
    def __init__(self, polys: List[List[str]], alpha: str, evals: List[str]):
        self.polys = polys
        self.alpha = alpha
        self.evals = evals

    def to_synapse(self, i: int) -> Prove:
        return Prove(index=i, poly=self.polys[i], eval=self.evals[i], alpha=self.alpha)


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

    def rpc_fft(self, poly: List[str], left: bool, inverse: bool) -> List[str]:
        with self.client.fft(poly, left, inverse) as response:
            if response.status_code != 200:
                bt.logging.error(
                    f"RPC request failed with status: {response.status_code}"
                )
                raise Exception("Failed to commit to the polynomial.")
            return response.json().get("poly")

    # Returns a random bivariate polynomial f(X, Y) as coefficients
    def rpc_random_poly(self) -> List[List[str]]:
        with self.client.random_poly() as response:
            if response.status_code != 200:
                bt.logging.error(
                    f"RPC request failed with status: {response.status_code}"
                )
                raise Exception("Failed to generate a random polynomial.")
            return response.json().get("poly")

    def rpc_worker_verify(
        self, i: int, proof: str, alpha: str, eval: str, commitment: str
    ) -> bool:
        with self.client.worker_verify(i, proof, alpha, eval, commitment) as response:
            if response.status_code != 200:
                bt.logging.error(
                    f"RPC request failed with status: {response.status_code}"
                )
                raise Exception("Failed to verify the proof.")
            return response.json().get("valid")

    def rpc_random_x(self) -> str:
        with self.client.random_point() as response:
            if response.status_code != 200:
                bt.logging.error(
                    f"RPC request failed with status: {response.status_code}"
                )
                raise Exception("Failed to generate a random x.")
            return response.json().get("point")

    def rpc_eval(self, poly: str, x: str) -> str:
        with self.client.eval(poly, x) as response:
            if response.status_code != 200:
                bt.logging.error(
                    f"RPC request failed with status: {response.status_code}"
                )
                raise Exception("Failed to evaluate the polynomial.")
            return response.json().get("y")

    def generate_challenge(self, machines_count: int) -> Challenge:
        """
        Generate a challenge for the miners to solve.
        """

        # Generate a random polynomial.
        poly = self.rpc_random_poly()
        alpha = self.rpc_random_x()
        evals = []
        for i in range(machines_count):
            fft_coeffs = self.rpc_fft(poly[i], left=True, inverse=True)
            eval = self.rpc_eval(fft_coeffs, alpha)
            evals.append(eval)

        return Challenge(polys=poly, alpha=alpha, evals=evals)

    async def forward(self):
        try:
            bt.logging.info("generating challenge for miners")
            challenge = self.generate_challenge(
                min(self.config.neuron.sample_size, self.metagraph.n.item())
            )
            bt.logging.info("sending challenge to miners")
            await self.query(challenge)
        except Exception as e:
            bt.logging.error(f"Failed to generate a query challenge: {e}")
            bt.logging.error("Retrying in 5 seconds...")
            time.sleep(5)

    def reward(
        self,
        challenge: Prove,
        response: Prove,
        timeout: float,
    ) -> np.float32:
        """
        Calculate the miner reward based on correctness and processing time.
        """

        # Don't bother verifying if we don't have all info
        if response.commitment is None or response.proof is None:
            bt.logging.warning("Received incomplete proof.")
            return 0.0

        # Don't even bother spending resources on verifying if the synapse
        # came in too late
        if response.dendrite.process_time > timeout:
            bt.logging.warning("Received proof which was too slow.")
            return 0.0

        # We take the proof and commitment from the response
        proof = response.proof
        commitment = response.commitment

        # We take the index, alpha and eval from the challenge
        # NOTE: it may be tempting to take the eval from the response
        # However, this would be a security vulnerability as the miner could
        # commit to a different polynomial entirely
        index = challenge.index
        alpha = challenge.alpha
        eval = challenge.eval

        valid = self.rpc_worker_verify(
            i=index, proof=proof, alpha=alpha, eval=eval, commitment=commitment
        )

        if not valid:
            bt.logging.warning("Invalid proof.")
            return 0.0

        return 1.0 - response.dendrite.process_time / timeout

    def get_rewards(
        self,
        challenge: Challenge,
        responses: List[Prove],
        timeout: float,
    ) -> np.array:
        """
        Calculate the miner rewards based on correctness and processing time.
        """
        # Get the fastest processing time.
        scores = [
            self.reward(challenge.to_synapse(response.index), response, timeout)
            for response in responses
        ]
        return np.array(scores, dtype=np.float32)

    async def query(self, challenge: Challenge):
        """
        Query the connected miners with a challenge
        Each miner will receive a different challenge and each challenge can be independently verified.
        The sum of all valid solutions can be used to generate a larger commitment, although not yet implemented, and not necessary for checking miner honesty.
        """
        miner_uids = get_random_uids(
            self, k=min(self.config.neuron.sample_size, self.metagraph.n.item())
        )

        if len(miner_uids) == 0:
            raise Exception("No miners available to query.")
        timeout = 30.0

        # We have to create seperate tasks for each miner to query them concurrently.
        # This is because the default dendrite implementation only supports
        # querying several axons with the same synapse.
        tasks = [
            asyncio.ensure_future(
                self.dendrite(
                    synapse=challenge.to_synapse(i),
                    deserialize=False,
                    timeout=timeout,
                    axons=[self.metagraph.axons[uid]],
                )
            )
            for i, uid in enumerate(miner_uids)
        ]

        responses = [response[0] for response in await asyncio.gather(*tasks)]
        if all(
            [
                response.commitment is None and response.proof is None
                for response in responses
            ]
        ):
            bt.logging.error("No responses received.")
            raise Exception("No responses received.")

        # Adjust the scores based on responses from miners.
        rewards = self.get_rewards(challenge, responses, timeout)
        bt.logging.info(f"Scored responses: {rewards}")

        # Update the scores based on the rewards.
        # You may want to define your own update_scores function for custom behavior.
        self.update_scores(rewards, miner_uids)


# The main function parses the configuration and runs the validator.
if __name__ == "__main__":
    with Validator() as validator:
        while True:
            bt.logging.info("Validator running...", time.time())
            time.sleep(5)
