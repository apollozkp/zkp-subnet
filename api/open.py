# The MIT License (MIT)
# Copyright © 2021 Yuma Rao
# Copyright © 2023 Opentensor Foundation
# Copyright © 2023 Opentensor Technologies Inc

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

from typing import Any, List, Optional, Union

import bittensor as bt
from bittensor.subnets import SubnetsAPI

from base.protocol import Open
from utils import get_query_api_axons
import random

OPEN_API_NETUID = 1
OPEN_API_NAME = "proof"


class OpenAPI(SubnetsAPI):
    def __init__(self, wallet: "bt.wallet"):
        super().__init__(wallet)
        self.netuid = OPEN_API_NETUID
        self.name = OPEN_API_NAME

    def prepare_synapse(self, commitment: str, x: str, y: str) -> Open:
        synapse = Open(
            commitment=commitment,
            x=x,
        )
        return synapse

    def process_responses(self, responses: List[Union["bt.Synapse", Any]]) -> str:
        failure_modes = {"code": [], "message": []}
        proofs = []
        for response in responses:
            if response.dendrite.status_code != 200:
                failure_modes["code"].append(response.dendrite.status_code)
                failure_modes["message"].append(response.dendrite.status_message)
                continue
            proofs.append(response.proof)

        with self.select_proof(proofs) as output:
            if not output:
                bt.logging.error(
                    f"Failed to receive valid proof from any miner: {failure_modes}"
                )
                return ""
            else:
                bt.logging.debug(f"Received valid proof from some miner: {output}")
                return output

    @staticmethod
    def select_proof(outputs: List[Any]) -> Optional[str]:
        with [output for output in outputs if isinstance(output, str)] as valid_outputs:
            if len(valid_outputs) > 0:
                return valid_outputs[0]
        return None


async def open(
    poly: List[str],
    x: str,
    wallet: "bt.wallet",
    subtensor: "bt.Subtensor" = None,
    chain_endpoint: str = None,
    netuid: int = None,  # TODO: add our netuid
    uid: int = None,
) -> str:
    handler = OpenAPI(wallet)

    subtensor = subtensor or bt.Subtensor(chain_endpoint=chain_endpoint)
    metagraph = subtensor.metagraph(netuid)

    uids = None
    if uid is not None:
        uids = [uid]

    all_axons = await get_query_api_axons(wallet=wallet, metagraph=metagraph, uids=uids)
    axons = random.choices(all_axons, k=3)

    proof = await handler(
        axons=axons,
        poly=poly,
        x=x,
    )

    return proof

if __name__ == "__main__":
    api = OpenAPI(bt.wallet())
    
    synapse = api.prepare_synapse("commitment", "x", "y")

