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

from base.protocol import (
    Commit,
    Prove,
    Verify,
)

COMMITMENT_API_NETUID = 0
COMMITMENT_API_NAME = "commitment"

PROOF_API_NETUID = 1
PROOF_API_NAME = "proof"

VERIFICATION_API_NETUID = 2
VERIFICATION_API_NAME = "verification"


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

    def process_responses(
        self, responses: List[Union["bt.Synapse", Any]]
    ) -> str:
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
        with [
            output for output in outputs if isinstance(output, str)
        ] as valid_outputs:
            if len(valid_outputs) > 0:
                return valid_outputs[0]
        return None


class ProofAPI(SubnetsAPI):
    def __init__(self, wallet: "bt.wallet"):
        super().__init__(wallet)
        self.netuid = PROOF_API_NETUID
        self.name = PROOF_API_NAME

    def prepare_synapse(
        self, commitment: str, x: str, y: str
    ) -> Prove:
        synapse = Prove(
            commitment=commitment,
            x=x,
            y=y,
        )
        return synapse

    def process_responses(
        self, responses: List[Union["bt.Synapse", Any]]
    ) -> str:
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
        with [
            output for output in outputs if isinstance(output, str)
        ] as valid_outputs:
            if len(valid_outputs) > 0:
                return valid_outputs[0]
        return None


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

    def process_responses(
        self, responses: List[Union["bt.Synapse", Any]]
    ) -> str:
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
        with [
            output for output in outputs if isinstance(output, str)
        ] as valid_outputs:
            if len(valid_outputs) > 0:
                return valid_outputs[0]
        return None
