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

    response_process_time = 0.0
    min_process_time = 0.0
    timeout = 10.0

    if missing_info:
        challenge.commitment = None

    if too_late: 
        response_process_time = 11.0

    if invalid_proof:
        challenge.y = "ea"

    if half_time:
        response_process_time = 5.0

    assert(
        validator.reward(
            challenge,
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
    challenge = validator.generate_challenge(10)
    resp = validator.client.prove(challenge.poly)
    assert resp.status_code == 200
    challenge.commitment = resp.json().get("result").get("commitment", "")
    challenge.y = resp.json().get("result").get("y", "")
    challenge.x = resp.json().get("result").get("x", "")
    challenge.proof = resp.json().get("result").get("proof", "")
    return challenge
