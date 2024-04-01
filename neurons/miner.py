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

import base64
import time
import typing

import bittensor as bt
from fourier import Client

import base

# import base miner class which takes care of most of the boilerplate
from base.miner import BaseMinerNeuron


class ClientConfig:
    def __init__(self, host: str = "127.0.0.1", port: int = 1337):
        self.host = host
        self.port = port


class MinerConfig(base.BaseConfig):
    def __init__(self):
        super().__init__()
        self.client_config = ClientConfig()

    def __str__(self):
        return str(self.__dict__)


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
        self.client = Client()
        self.client.start()

    async def blacklist(self, synapse: base.protocol.Trace) -> typing.Tuple[bool, str]:
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

    async def priority(self, synapse: base.protocol.Trace) -> float:
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

    def commit(self, synapse: base.protocol.Commit) -> base.protocol.Commit:
        """
        Query the connected ZKG RPC server (commit).
        """
        with self.client.commit(synapse.poly) as resp:
            if resp.get("error"):
                bt.log.error(f"Error committing: {resp.get('error')}")
                return synapse
            elif resp.get("result").get("commitment"):
                synapse.commitment = resp.get("result").get("commitment")
            else:
                bt.log.error(f"Error committing: {resp}")
        return synapse

    def open(self, synapse: base.protocol.Open) -> base.protocol.Open:
        """
        Query the connected ZKG RPC server (open).
        """
        with self.client.open(synapse.commitment, synapse.x) as resp:
            if resp.get("error"):
                bt.log.error(f"Error opening: {resp.get('error')}")
                return synapse
            elif resp.get("result").get("proof"):
                synapse.proof = resp.get("result").get("proof")
            else:
                bt.log.error(f"Error opening: {resp}")
        return synapse

    def verify(self, synapse: base.protocol.Verify) -> base.protocol.Verify:
        """
        Query the connected ZKG RPC server (verify).
        """
        with self.client.verify(synapse.commitment) as resp:
            if resp.get("error"):
                bt.log.error(f"Error verifying: {resp.get('error')}")
                return synapse
            elif resp.get("result").get("valid"):
                synapse.valid = resp.get("result").get("valid")
            else:
                bt.log.error(f"Error verifying: {resp}")
        return synapse


# This is the main function, which runs the miner.
if __name__ == "__main__":
    with Miner() as miner:
        while True:
            bt.logging.info("Miner running...", time.time())
            time.sleep(5)
