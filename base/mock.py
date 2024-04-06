# The MIT License (MIT)
# Copyright © 2023 Opentensor Foundation

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

import asyncio
import base64
import random
import bittensor as bt

from typing import List


class MockSubtensor(bt.MockSubtensor):
    def __init__(self, netuid=1, n=16, wallet=None, network="mock"):
        super().__init__(network=network)

        if not self.subnet_exists(netuid):
            self.create_subnet(netuid)

        # Register ourself (the validator) as a neuron at uid=0
        if wallet is not None:
            self.force_register_neuron(
                netuid=netuid,
                hotkey=wallet.hotkey.ss58_address,
                coldkey=wallet.coldkey.ss58_address,
                balance=100000,
                stake=100000,
            )

        # Register n mock neurons who will be miners
        for i in range(1, n + 1):
            self.force_register_neuron(
                netuid=netuid,
                hotkey=f"miner-hotkey-{i}",
                coldkey=f"mock-coldkey-{i}",
                balance=100000,
                stake=100000,
            )


class MockMetagraph(bt.metagraph):
    def __init__(self, netuid=1, network="mock", subtensor=None):
        super().__init__(netuid=netuid, network=network, sync=False)

        if subtensor is not None:
            self.subtensor = subtensor
        self.sync(subtensor=subtensor)

        for axon in self.axons:
            axon.ip = "127.0.0.0"
            axon.port = 8091

        bt.logging.info(f"Metagraph: {self}")
        bt.logging.info(f"Axons: {self.axons}")

class MockDendrite(bt.dendrite):
    def __init__(self, wallet):
        super().__init__(wallet)

    async def forward(
        self,
        axons: List[bt.axon],
        synapse: bt.Synapse = bt.Synapse(),
        timeout: float = 10,
        deserialize: bool = False,
        run_async: bool = True,
        streaming: bool = False,
    ):
        if streaming:
            raise NotImplementedError("Streaming not implemented yet.")

        async def query_all_axons(streaming: bool):
            async def single_axon_response(i, axon):
                start_time = time.time()
                s = synapse.copy()
                s = self.preprocess_synapse_for_request(axon, s, timeout)
                process_time = random.random()
                if process_time < timeout:
                    s.dendrite.process_time = str(time.time() - start_time)
                    s.dendrite.status_code = 200
                    s.dendrite.status_message = "OK"
                    synapse.dendrite.process_time = str(process_time)
                else:
                    s.dendrite.status_code = 408
                    s.dendrite.status_message = "Timeout"
                    synapse.dendrite.process_time = str(timeout)

                if deserialize:
                    return s.deserialize()
                else:
                    return s

            return await asyncio.gather(
                *(
                    single_axon_response(i, target_axon)
                    for i, target_axon in enumerate(axons)
                )
            )

        return await query_all_axons(streaming)

    def __str__(self) -> str:
        return "MockDendrite({})".format(self.keypair.ss58_address)
