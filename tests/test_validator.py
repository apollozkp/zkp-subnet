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

import pytest

from base.protocol import Prove
from neurons.validator import Validator


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
    validator = Validator(config)
    yield validator
    validator.subtensor.reset()
    validator.stop_run_thread()


@pytest.mark.parametrize(
    "missing_info,too_late,invalid_proof,half_time,expected_value",
    [
        (False, False, False, False, 1.0),
        (True, False, False, False, 0.0),
        (False, True, False, False, 0.0),
        (False, False, True, False, 0.0),
        (False, False, False, True, 0.5),
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
    validator = setup_validator
    challenge = make_proof(validator)
    simulated_response = challenge

    response_process_time = 0.0
    min_process_time = 0.0
    timeout = 10.0

    if missing_info:
        simulated_response.commitment = None

    if too_late:
        response_process_time = 11.0

    if invalid_proof:
        # xor a character to change the proof
        changed_proof = chr(ord(simulated_response.proof[0]) ^ 1) + simulated_response.proof[1:]
        simulated_response.proof = changed_proof

    if half_time:
        response_process_time = 5.0

    print("challenge", challenge)
    print("simulated_response", simulated_response)

    assert (
        validator.reward(
            challenge,
            simulated_response,
            response_process_time,
            min_process_time,
            timeout,
        )
        == expected_value
    )


@pytest.mark.asyncio
async def test_validator_forward(setup_validator):
    validator = setup_validator

    proof = make_proof(validator)

    await validator.query(proof)

    for score in validator.scores:
        assert score > 0.0


def make_proof(validator):
    challenge = validator.generate_challenge()
    with validator.client.commit(challenge.poly) as resp:
        assert resp.status_code == 200
        commitment = resp.json().get("result").get("commitment")

    with validator.client.open(challenge.poly, challenge.x) as resp:
        assert resp.status_code == 200
        proof = resp.json().get("result").get("proof")

    with validator.client.verify(proof, challenge.x, challenge.y, commitment) as resp:
        assert resp.status_code == 200
        assert resp.json().get("result").get("valid")

    challenge.commitment = commitment
    challenge.proof = proof
    return challenge

