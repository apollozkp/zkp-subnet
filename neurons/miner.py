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

    def forward(self, synapse: Prove) -> Prove:
        """
        Query the connected ZKG RPC server (prove).
        """
        bt.logging.info("Received synapse on prove")
        with self.client.prove(synapse.poly) as resp:
            error = resp.json().get("error")
            if error:
                bt.log.error(f"Error proving: {error}")
            else:
                synapse.commitment = resp.json().get("result").get("commitment", "")
                synapse.y = resp.json().get("result").get("y", "")
                synapse.x = resp.json().get("result").get("x", "")
                synapse.proof = resp.json().get("result").get("proof", "")
        bt.logging.info("Returning synapse")
        return synapse

# This is the main function, which runs the miner.
if __name__ == "__main__":
    with Miner() as miner:
        while True:
            bt.logging.info("Miner running...", time.time())
            time.sleep(5)
