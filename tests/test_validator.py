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
    "proof_bytes,response_proof,response_process_time,min_process_time,timeout,expected_value",
    [
        (bytes("hi", "utf-8"), bytes("hi", "utf-8"), 2.6, 2.6, 10.0, 1.0),
        (bytes("hi", "utf-8"), bytes("hello", "utf-8"), 2.6, 2.6, 10.0, 0.0),
        (bytes("hi", "utf-8"), bytes("hi", "utf-8"), 11.6, 2.6, 10.0, 0.0),
        (bytes("hi", "utf-8"), bytes("hi", "utf-8"), 7.5, 5.0, 10.0, 0.5),
    ],
)
def test_reward(
    proof_bytes,
    response_proof,
    response_process_time,
    min_process_time,
    timeout,
    expected_value,
):
    validator = setup_validator
    assert(
        validator.reward(
            proof_bytes,
            response_proof,
            response_process_time,
            min_process_time,
            timeout,
        )
        == expected_value
    )


@pytest.mark.asyncio
async def test_validator_forward(compile_prover_lib, setup_validator):
    validator = setup_validator
    
    poly = ["123", "456"]
    bogus_prove = Prove(poly=poly)
    
    await validator.query(bogus_prove)
    
    for score in validator.scores:
        assert score > 0.0
