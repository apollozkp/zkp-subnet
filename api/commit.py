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

from base.protocol import Commit
from utils import get_query_api_axons

import random

COMMITMENT_API_NETUID = 0
COMMITMENT_API_NAME = "commitment"


class CommitmentAPI(SubnetsAPI):
    def __init__(self, wallet: "bt.wallet"):
        super().__init__(wallet)
        self.netuid = COMMITMENT_API_NETUID
        self.name = COMMITMENT_API_NAME

    def prepare_synapse(self, p: str) -> Commit:
        synapse = Commit(
            polynomial=p,
        )
        return synapse

    def process_responses(self, responses: List[Union["bt.Synapse", Any]]) -> str:
        failure_modes = {"code": [], "message": []}
        commitments = []
        for response in responses:
            if response.dendrite.status_code != 200:
                failure_modes["code"].append(response.dendrite.status_code)
                failure_modes["message"].append(response.dendrite.status_message)
                continue
            commitments.append(response.commitment)

        with self.select_commitment(commitments) as output:
            if not output:
                bt.logging.error(
                    f"Failed to receive valid proof from any miner: {failure_modes}"
                )
                return ""
            else:
                bt.logging.debug(f"Received valid proof from some miner: {output}")
                return output

    # Filter out invalid responses and select a final response from the valid ones.
    @staticmethod
    def select_commitment(outputs: List[Any]) -> Optional[str]:
        with [output for output in outputs if isinstance(output, str)] as valid_outputs:
            if len(valid_outputs) > 0:
                return valid_outputs[0]
        return None


async def commit(
    poly: List[str],
    wallet: "bt.wallet",
    subtensor: "bt.Subtensor" = None,
    chain_endpoint: str = None,
    netuid: int = None,  # TODO: add our netuid
    uid: int = None,
) -> str:
    handler = CommitmentAPI(wallet)

    subtensor = subtensor or bt.Subtensor(chain_endpoint=chain_endpoint)
    metagraph = subtensor.metagraph(netuid)

    uids = None
    if uid is not None:
        uids = [uid]

    all_axons = await get_query_api_axons(wallet=wallet, metagraph=metagraph, uids=uids)
    axons = random.choices(all_axons, k=3)

    commitment = await handler(
        axons=axons,
        poly=poly,
    )

    return commitment
