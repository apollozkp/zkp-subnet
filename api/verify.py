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

import random
from typing import Any, List, Optional, Union

import bittensor as bt
from bittensor.subnets import SubnetsAPI

from base.protocol import Verify
from utils import get_query_api_axons

VERIFICATION_API_NETUID = 2
VERIFICATION_API_NAME = "verification"


class VerificationAPI(SubnetsAPI):
    def __init__(self, wallet: "bt.wallet"):
        super().__init__(wallet)
        self.netuid = VERIFICATION_API_NETUID
        self.name = VERIFICATION_API_NAME

    def prepare_synapse(
        self,
        commitment: str,
        x: str,
        y: str,
        proof: str,
    ) -> Verify:
        synapse = Verify(
            commitment=commitment,
            x=x,
            y=y,
            proof=proof,
        )
        return synapse

    def process_responses(self, responses: List[Union["bt.Synapse", Any]]) -> bool:
        failure_modes = {"code": [], "message": []}
        proofs = []
        for response in responses:
            if response.dendrite.status_code != 200:
                failure_modes["code"].append(response.dendrite.status_code)
                failure_modes["message"].append(response.dendrite.status_message)
                continue
            proofs.append(response.proof)

        with self.select_valid(proofs) as output:
            if not output:
                bt.logging.error(
                    f"Failed to receive valid proof from any miner: {failure_modes}"
                )
                return ""
            else:
                bt.logging.debug(f"Received valid proof from some miner: {output}")
                return output

    @staticmethod
    def select_valid(outputs: List[Any]) -> Optional[str]:
        with [
            output for output in outputs if isinstance(output, bool)
        ] as valid_outputs:
            if len(valid_outputs) > 0:
                return valid_outputs[0]
        return None


async def verify(
    commitment: str,
    x: str,
    y: str,
    proof: str,
    wallet: "bt.wallet",
    subtensor: "bt.Subtensor" = None,
    chain_endpoint: str = None,
    netuid: int = None,  # TODO: add our netuid
    uid: int = None,
) -> str:
    handler = VerificationAPI(wallet)

    subtensor = subtensor or bt.Subtensor(chain_endpoint=chain_endpoint)
    metagraph = subtensor.metagraph(netuid)

    uids = None
    if uid is not None:
        uids = [uid]

    all_axons = await get_query_api_axons(wallet=wallet, metagraph=metagraph, uids=uids)
    axons = random.choices(all_axons, k=3)

    valid = await handler(
        axons=axons,
        commitment=commitment,
        x=x,
        y=y,
        proof=proof,
    )

    return valid
