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
import base64
import bittensor as bt

import base

# import base miner class which takes care of most of the boilerplate
from base.miner import BaseMinerNeuron
from utils.rust import make_proof

from utils.cairo_generator import LIB_PATH

class Miner(BaseMinerNeuron):
    def __init__(self, config=None):
        super(Miner, self).__init__(config=config)

    async def forward(
        self, synapse: base.protocol.Trace
    ) -> base.protocol.Trace:
        return forward(synapse)

    async def blacklist(
        self, synapse: base.protocol.Trace
    ) -> typing.Tuple[bool, str]:
        try:
            uid = self.metagraph.hotkeys.index(synapse.dendrite.hotkey)
            if self.config.blacklist.force_validator_permit:
                # If the config is set to force validator permit, then we should only allow requests from validators.
                if not self.metagraph.validator_permit[uid]:
                    bt.logging.warning(
                        f"Blacklisting a request from non-validator hotkey {synapse.dendrite.hotkey}"
                    )
                    return True, "Non-validator hotkey"

            bt.logging.trace(
                f"Not Blacklisting recognized hotkey {synapse.dendrite.hotkey}"
            )
            return False, "Hotkey recognized!"
        except:
            if self.config.blacklist.allow_non_registered:
                if self.config.blacklist.force_validator_permit:
                    bt.logging.warning(
                        f"Blacklisting a request from unregistered non-validator hotkey {synapse.dendrite.hotkey}"
                    )
                    return True, "Unrecognized hotkey"

                return False, "Allowing unregistered hotkey"
            else:
                bt.logging.warning(
                    f"Blacklisting a request from unregistered hotkey {synapse.dendrite.hotkey}"
                )
                return True, "Unrecognized hotkey"

    async def priority(self, synapse: base.protocol.Trace) -> float:
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

def forward(synapse: base.protocol.Trace, lib_path: str=LIB_PATH) -> base.protocol.Trace:
    # Decode the strings to bytes for Rust.
    main_trace = base64.b64decode(synapse.main_trace)
    pub_inputs = base64.b64decode(synapse.pub_inputs)

    # Generate the actual proof.
    proof = make_proof(main_trace, pub_inputs, lib_path)

    # And re-encode back to base64 strings; because Python apparently doesn't know that JSON
    # can just take byte arrays, and so we have to coddle it :)
    proof = base64.b64encode(proof)

    synapse.proof = proof
    return synapse

# This is the main function, which runs the miner.
if __name__ == "__main__":
    with Miner() as miner:
        while True:
            bt.logging.info("Miner running...", time.time())
            time.sleep(5)
