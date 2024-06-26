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
import typing

import bittensor as bt

# import base miner class which takes care of most of the boilerplate
from base.miner import BaseMinerNeuron
from base.protocol import Prove


class Miner(BaseMinerNeuron):
    """
    Miner class for the ZKG network.
    The miner handles the following tasks:
    - prove: Commits to a polynomial and computes an opening proof of it.
    """

    def __init__(self, config=None):
        super(Miner, self).__init__(config=config)

    def rpc_commit(self, i: int, poly: str) -> str:
        with self.client.worker_commit(i, poly) as response:
            if response.status_code != 200:
                bt.logging.error(
                    f"RPC request failed with status: {response.status_code}"
                )
                raise Exception("Failed to commit to the polynomial.")
            return response.json().get("commitment")

    def rpc_open(self, i: int, poly: str, x: str) -> typing.Tuple[str, str]:
        with self.client.worker_open(i, poly, x) as response:
            if response.status_code != 200:
                bt.logging.error(
                    f"RPC request failed with status: {response.status_code}"
                )
                raise Exception("Failed to verify the proof.")
            return response.json().get("eval"), response.json().get("proof")

    def rpc_commit_and_open(
        self, i: int, poly: str, alpha: str
    ) -> typing.Tuple[str, str]:
        commitment = self.rpc_commit(i, poly)
        eval, proof = self.rpc_open(i, poly, alpha)
        return commitment, eval, proof

    async def blacklist(self, synapse: Prove) -> typing.Tuple[bool, str]:
        """
        Check if the hotkey is blacklisted.
        """
        try:
            uid = self.metagraph.hotkeys.index(synapse.dendrite.hotkey)
            bt.logging.trace(
                f"Not Blacklisting recognized hotkey {synapse.dendrite.hotkey} with uid"
                f" {uid}"
            )
            return False, "Hotkey recognized!"
        except Exception:
            if self.config.blacklist.allow_non_registered:
                return False, "Allowing unregistered hotkey"
            else:
                bt.logging.warning(
                    "Blacklisting a request from unregistered hotkey"
                    f" {synapse.dendrite.hotkey}"
                )
                return True, "Unrecognized hotkey"

    async def priority(self, synapse: Prove) -> float:
        """
        Get the priority of the hotkey.
        """
        try:
            caller_uid = self.metagraph.hotkeys.index(
                synapse.dendrite.hotkey
            )  # Get the caller index.
            priority = float(
                self.metagraph.S[caller_uid]
            )  # Return the stake as the priority.
            bt.logging.trace(
                f"Prioritizing {synapse.dendrite.hotkey} with value: ", priority
            )
            return priority

        except Exception:
            bt.logging.warning(
                f"Failed to prioritize {synapse.dendrite.hotkey}. Defaulting to 0."
            )
            return 0.0

    def forward(self, synapse: Prove) -> Prove:
        """
        Query the connected ZKG RPC server (prove).
        """
        try:
            bt.logging.info("Received synapse on prove, starting proof generation...")
            before = time.perf_counter()
            commitment, eval, proof = self.rpc_commit_and_open(
                synapse.index, synapse.poly, synapse.alpha
            )
            elapsed = time.perf_counter() - before
            bt.logging.info(f"Proof generation completed in {elapsed} seconds")

            synapse = Prove(
                # Send back empty values to save bandwidth
                index=int(synapse.index),
                poly=[],
                alpha=None,
                # These are the only values we care about sending back
                eval=eval,
                commitment=commitment,
                proof=proof,
            )

            bt.logging.info("Returning synapse")
            return synapse

        except Exception as e:
            bt.logging.error(f"Failed to forward synapse: {e}")
            return synapse


# This is the main function, which runs the miner.
if __name__ == "__main__":
    with Miner() as miner:
        while True:
            bt.logging.info("Miner running...", time.time())
            time.sleep(5)
