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
from fourier import Client

# import base miner class which takes care of most of the boilerplate
from base.miner import BaseMinerNeuron
from base.protocol import Commit, Open, Verify


class Miner(BaseMinerNeuron):
    """
    Miner class for the ZKG network.
    The miner handles the following tasks:
    - commit: Compute the commitment of a polynomial.
    - open: Compute the proof of a commitment.
    - verify: Verify the proof of a commitment.
    """

    def __init__(self, config=None):
        super(Miner, self).__init__(config=config)

        # Start the local ZKG RPC server.
        PORT = 1337
        self.client = Client(port=PORT)
        self.client.start()

        self.axon.attach(
            forward_fn=self.commit_polynomial,
            priority_fn=self.commit_polynomial_priority,
            blacklist_fn=self.commit_polynomial_blacklist,
        ).attach(
            forward_fn=self.open_polynomial,
            priority_fn=self.open_polynomial_priority,
            blacklist_fn=self.open_polynomial_blacklist,
        ).attach(
            forward_fn=self.verify_proof,
            priority_fn=self.verify_proof_priority,
            blacklist_fn=self.verify_proof_blacklist,
        )

    async def forward(self, synapse: bt.Synapse) -> bt.Synapse:
        bt.logging.info("Received synapse on forward", synapse)
        pass

    async def blacklist(self, synapse: bt.Synapse) -> typing.Tuple[bool, str]:
        """
        Check if the hotkey is blacklisted.
        """
        try:
            uid = self.metagraph.hotkeys.index(synapse.dendrite.hotkey)
            bt.logging.trace(
                f"Not Blacklisting recognized hotkey {synapse.dendrite.hotkey} with uid"
                f" {uid}"
            )
            return False, ""
        except Exception:
            if self.config.blacklist.allow_non_registered:
                return False
            else:
                bt.logging.warning(
                    "Blacklisting a request from unregistered hotkey"
                    f" {synapse.dendrite.hotkey}"
                )
                return True, ""

    async def priority(self, synapse: bt.Synapse) -> float:
        """
        Get the priority of the hotkey.
        """
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

    async def commit_polynomial(self, synapse: Commit) -> Commit:
        """
        Query the connected ZKG RPC server (commit).
        """
        bt.logging.info("Received synapse on commit", synapse)
        with self.client.commit(synapse.poly) as resp:
            error = resp.json().get("error")
            if error:
                bt.log.error(f"Error committing: {error}")
            synapse.commitment = resp.json().get("result").get("commitment", "")
        bt.logging.info("Returning synapse", synapse)
        return synapse

    async def open_polynomial(self, synapse: Open) -> Open:
        """
        Query the connected ZKG RPC server (open).
        """
        bt.logging.info("Received synapse on open", synapse)
        with self.client.open(synapse.poly, synapse.x) as resp:
            error = resp.json().get("error")
            if error:
                bt.log.error(f"Error opening: {error}")
            synapse.proof = resp.json().get("result").get("proof", "")
        return synapse

    async def verify_proof(self, synapse: Verify) -> Verify:
        """
        Query the connected ZKG RPC server (verify).
        """
        bt.logging.info("Received synapse on verify", synapse)
        with self.client.verify(synapse.commitment) as resp:
            error = resp.json().get("error")
            if error:
                bt.log.error(f"Error verifying: {error}")
            synapse.valid = resp.json().get("result").get("valid", False)
        return synapse

    async def commit_polynomial_blacklist(self, synapse: Commit) -> typing.Tuple[bool, str]:
        return await self.blacklist(synapse)

    async def commit_polynomial_priority(self, synapse: Commit) -> float:
        return await self.priority(synapse)

    async def open_polynomial_blacklist(self, synapse: Open) -> typing.Tuple[bool, str]:
        return await self.blacklist(synapse)

    async def open_polynomial_priority(self, synapse: Open) -> float:
        return await self.priority(synapse)

    async def verify_proof_blacklist(self, synapse: Verify) -> typing.Tuple[bool, str]:
        return await self.blacklist(synapse)

    async def verify_proof_priority(self, synapse: Verify) -> float:
        return await self.priority(synapse)

# This is the main function, which runs the miner.
if __name__ == "__main__":
    with Miner() as miner:
        while True:
            bt.logging.info("Miner running...", time.time())
            time.sleep(5)
