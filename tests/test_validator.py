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
from typing import List, Tuple

import pytest

from base.protocol import Prove
from neurons.validator import Challenge, Validator
from tests.conftest import (
    TEST_BINARY,
    TEST_MACHINES_SCALE,
    TEST_PRECOMPUTE_PATH,
    TEST_SCALE,
    TEST_SETUP_PATH,
)

TEST_MACHINE_COUNT = 2


@pytest.fixture(scope="module")
def setup_validator():
    config = Validator.config()
    config.mock = True
    config.netuid = 10
    config.neuron.sample_size = 50
    config.neuron.dont_save_events = True
    config.neuron.device = "cpu"
    config.wallet.name = "valimock"
    config.wallet.hotkey = "valimockhotkey"

    # Client setup
    config.scale = TEST_SCALE
    config.machines_scale = TEST_MACHINES_SCALE
    config.setup_path = TEST_SETUP_PATH
    config.precompute_path = TEST_PRECOMPUTE_PATH
    config.prover_path = f"./{TEST_BINARY}"

    validator = Validator(config)
    yield validator
    validator.subtensor.reset()
    validator.stop_run_thread()


@pytest.mark.parametrize(
    "missing_info,too_late,invalid_proof,half_time,expected_value",
    [
        (False, False, False, False, [1.0, 1.0]),
        (True, False, False, False, [0.0, 1.0]),
        (False, True, False, False, [0.0, 1.0]),
        (False, False, True, False, [0.0, 1.0]),
        (False, False, False, True, [0.5, 1.0]),
    ],
)
def test_reward(
    setup_validator,
    missing_info,
    too_late,
    invalid_proof,
    half_time,
    expected_value,
):

    def change_proof(proof: str):
        # Update if we change to base64
        decoded_proof = base64.b64decode(proof)
        n_bytes = len(decoded_proof)
        # LE or BE doesn't matter, just need >1 bit to change
        proof_plus_one = int.from_bytes(decoded_proof, "big") + 1 % 2 ** (n_bytes * 8)
        proof_plus_one_bytes = proof_plus_one.to_bytes(n_bytes, "big")
        return base64.b64encode(proof_plus_one_bytes).decode()

    validator = setup_validator
    challenge, responses, is_valid = make_proofs(validator)

    simulated_responses = responses.copy()
    for simulated_response in simulated_responses:
        simulated_response.dendrite.process_time = 0.0

    timeout = 10.0

    if missing_info:
        simulated_responses[0].commitment = None

    if too_late:
        simulated_responses[0].dendrite.process_time = 11.0

    if invalid_proof:
        simulated_responses[0].proof = change_proof(simulated_responses[0].proof)

    if half_time:
        simulated_responses[0].dendrite.process_time = 5.0

    print("challenge", challenge)
    print("simulated_response", simulated_response)

    rewards = validator.get_rewards(
        challenge,
        simulated_responses,
        timeout,
    )
    print("rewards", rewards)

    assert len(rewards) == len(expected_value)
    for reward, expected in zip(rewards, expected_value):
        assert reward == expected


def make_proofs(validator) -> Tuple[Challenge, List[Prove], List[bool]]:
    challenge = validator.generate_challenge(TEST_MACHINE_COUNT)

    responses = []
    for i in range(TEST_MACHINE_COUNT):
        poly = challenge.polys[i]
        point = challenge.alpha
        with validator.client.worker_commit(i, poly) as resp:
            commitment = resp.json().get("commitment")

        with validator.client.worker_open(i, poly, point) as resp:
            eval = resp.json().get("eval")
            proof = resp.json().get("proof")

        response = Prove(
            # Send back empty values to save bandwidth
            index=i,
            poly=[],
            alpha=None,
            # These are the only values we care about sending back
            eval=eval,
            commitment=commitment,
            proof=proof,
        )
        responses.append(response)

    is_valid = []
    for response in responses:
        with validator.client.worker_verify(
            response.index,
            response.proof,
            challenge.alpha,
            response.eval,
            response.commitment,
        ) as resp:
            assert resp.status_code == 200
            valid = resp.json().get("valid")
        is_valid.append(valid)

    return challenge, responses, is_valid
