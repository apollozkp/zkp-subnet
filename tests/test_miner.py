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
import pytest
import bittensor
from neurons.miner import forward, Miner
from utils.cairo_generator import generate_random_cairo_trace
from base.neuron import BaseNeuron
from base.protocol import Trace
from bittensor.mock.wallet_mock import get_mock_wallet

@pytest.fixture(scope="module")
def setup_miner():
    config = BaseNeuron.config()
    config.mock = True
    config.netuid = 1
    config.wallet.name = "minermock"
    config.wallet.hotkey = "minermockhotkey"
    config.neuron.dont_save_events = True
    miner = Miner(config)
    yield miner
    miner.subtensor.reset()
    miner.stop_run_thread()

@pytest.mark.parametrize("n", [10, 100, 1000])
def test_miner_forward(compile_prover_lib, n):
    compiled_path = compile_prover_lib
    trace, proof = generate_random_cairo_trace(n, n, compiled_path)
    return_trace = forward(trace, compiled_path)
    proof_bytes = base64.b64decode(return_trace.proof)
    assert proof_bytes == proof

@pytest.mark.asyncio
@pytest.mark.parametrize("allow_non_registered,force_vpermit", [
    (False, False),
    (True, False),
    (False, True),
    (True, True)
])
async def test_miner_blacklist(setup_miner, allow_non_registered, force_vpermit):
    miner = setup_miner
    miner.config.blacklist.allow_non_registered = allow_non_registered
    miner.config.blacklist.force_validator_permit = force_vpermit
    uid = miner.metagraph.hotkeys.index(miner.wallet.hotkey.ss58_address)
    miner.metagraph.validator_permit[uid] = force_vpermit

    synapse = Trace(main_trace="a", pub_inputs="b")
    synapse.dendrite.hotkey = miner.wallet.hotkey.ss58_address

    outside_synapse = Trace(main_trace="a", pub_inputs="b")
    outside_wallet = get_mock_wallet()
    outside_synapse.dendrite.hotkey = outside_wallet.hotkey.ss58_address

    bl1, _ = await miner.blacklist(synapse)
    bl2, _ = await miner.blacklist(outside_synapse)

    assert not bl1
    if allow_non_registered:
        if force_vpermit:
            assert bl2
        else:
            assert not bl2
    else:
        assert bl2
    
@pytest.mark.asyncio
async def test_miner_priority(setup_miner):
    miner = setup_miner
    synapse = Trace(main_trace="a", pub_inputs="b")
    synapse.dendrite.hotkey = miner.wallet.hotkey.ss58_address
    assert await miner.priority(synapse) > 0
