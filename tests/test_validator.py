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
from neurons.validator import Validator, reward, query
from base.protocol import Trace

@pytest.fixture(scope="module")
def setup_validator():
    config = Validator.config()
    config.mock = True
    config.netuid = 10
    config.neuron.sample_size = 50
    config.neuron.dont_save_events = True
    config.wallet.name = "valimock"
    config.wallet.hotkey = "valimockhotkey"
    validator = Validator(config)
    yield validator
    validator.subtensor.reset()
    validator.stop_run_thread()

@pytest.mark.parametrize("proof_bytes,response_proof,expected_value", [
    (bytes("hi", "utf-8"), bytes("hi", "utf-8"), 1.0),
    (bytes("hi", "utf-8"), bytes("hello", "utf-8"), 0.0),
])
def test_reward(proof_bytes, response_proof, expected_value):
    assert reward(proof_bytes, response_proof) == expected_value

@pytest.mark.asyncio
async def test_validator_forward(compile_prover_lib, setup_validator):
    compiled_path = compile_prover_lib
    validator = setup_validator

    bogus_trace = Trace(main_trace="hello", pub_inputs="world")
    response = bytes("abc", "utf-8")

    rewards = await query(validator, bogus_trace, response)

    for reward in rewards:
        assert reward == 1.0 or reward == 0.0
