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
from bittensor.mock.wallet_mock import get_mock_wallet

from base.neuron import BaseNeuron
from base.protocol import Prove
from neurons.miner import Miner
from tests.conftest import (
    TEST_BINARY,
    TEST_MACHINES_SCALE,
    TEST_PRECOMPUTE_PATH,
    TEST_SCALE,
    TEST_SETUP_PATH,
)

TEST_POLY = [
    "aUXcXE/02sinJ4ybjw1GEzIM+H/5R/Iayb9CMn7BlEg",
    "aOQMCI2Ce8zgLO80vcjBK7Al++oEe8bADAyMXJJbf68",
    "ZygfrBZOk0i4BpO6MNXU4xHeWHjrPSDjSlhQe0hLJDw",
    "X3w3fa5rnZq6113BXk//n+dSDR+FIkyV9IX0SXgVTFo",
    "LYXDdqRAtuJcP3wRVZtqJ2hAI/NsPXoKzX59AZ3jmcc",
    "Sm+5XwJBs1g3ceeZEgyHquPIQ+zbUKOCVKkuGYloki8",
    "EAUHn5bsQSpxn+Lp+mfUIdmPtN7EGBRZ5ZQw9dUCvSo",
    "ZJYLhpIGLcsBwP+6xWlHiomtiA7Tyd9xC+1c519IRpM",
    "A8KIIVWkR2Qr0h+xzyVT+AlVcT8Ju7vZck4sv9ixnUE",
    "CrB/7LWe40NfYSn81gLLUZ5W17QmlBYz43o7Z2okgw8",
    "EvpYYUWe/7rmVIJ9mL/f6lVF3fi7lihXlGPaIfF0YrU",
    "amKWoDdtgHUw2wnci7Bp/97D11QUl7gscioZnWt8WwY",
    "FT0sgbVNfhw+g+phx/Zv2IFV8XE+5YHivoQ4yp/uGgI",
    "IWvMxK6X/j4dSyHDdcRhQPoVPnhoIBpDSAiJBHrNDC0",
    "OBvU/pJOsQ4I8qIn09sgg6oOWh9mHNPHAsS4qTheeDk",
    "cjp2QP1+ZUcxMVY6tVFJFqyGHCaVzmUT5QYeWX5eGoE",
]


TEST_WORKER_INDEX = 0
TEST_POINT = "RWAG//VkEtMp1SeQHQKHelgaic+md8qWPrnWgHZiNMw"
TEST_EVAL = "KXMqHg4HSrBe5qnld5TFrRlluYtsjG7N6WrHduoG/1s"

TEST_SYNAPSE = Prove(
    index=TEST_WORKER_INDEX, poly=TEST_POLY, alpha=TEST_POINT, eval=TEST_EVAL
)


@pytest.fixture(scope="module")
def setup_miner():
    config = BaseNeuron.config()
    config.mock = True
    config.netuid = 1
    config.wallet.name = "minermock"
    config.wallet.hotkey = "minermockhotkey"
    config.neuron.dont_save_events = True

    # Client configuration
    config.scale = TEST_SCALE
    config.machines_scale = TEST_MACHINES_SCALE
    config.setup_path = TEST_SETUP_PATH
    config.precompute_path = TEST_PRECOMPUTE_PATH
    config.prover_path = f"./{TEST_BINARY}"

    miner = Miner(config)
    yield miner
    miner.subtensor.reset()
    miner.stop_run_thread()


@pytest.mark.parametrize("include_point", [True, False])
def test_miner_forward(setup_miner, include_point):
    miner = setup_miner

    with miner.client.worker_commit(
        i=TEST_SYNAPSE.index, poly=TEST_SYNAPSE.poly
    ) as resp:
        assert resp.status_code == 200
        commitment = resp.json().get("commitment")

    with miner.client.worker_open(
        i=TEST_SYNAPSE.index, poly=TEST_SYNAPSE.poly, x=TEST_SYNAPSE.alpha
    ) as resp:
        assert resp.status_code == 200
        eval = resp.json().get("eval")
        proof = resp.json().get("proof")

    with miner.client.worker_verify(
        i=TEST_SYNAPSE.index,
        proof=proof,
        alpha=TEST_SYNAPSE.alpha,
        eval=eval,
        commitment=commitment,
    ) as resp:
        assert resp.status_code == 200
        valid = resp.json().get("valid")

    assert valid

    synapse = TEST_SYNAPSE
    if not include_point:
        synapse.alpha = None

    ret_synapse = miner.forward(TEST_SYNAPSE)

    if include_point:
        assert ret_synapse.commitment == commitment
        assert ret_synapse.proof == proof


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "allow_non_registered,force_vpermit",
    [(False, False), (True, False), (False, True), (True, True)],
)
async def test_miner_blacklist(setup_miner, allow_non_registered, force_vpermit):
    miner = setup_miner
    miner.config.blacklist.allow_non_registered = allow_non_registered
    miner.config.blacklist.force_validator_permit = force_vpermit
    uid = miner.metagraph.hotkeys.index(miner.wallet.hotkey.ss58_address)
    miner.metagraph.validator_permit[uid] = force_vpermit

    poly = ["123", "456"]
    synapse = Prove(index=0, poly=poly, alpha="789")
    synapse.dendrite.hotkey = miner.wallet.hotkey.ss58_address

    outside_synapse = Prove(index=0, poly=poly, alpha="789")
    outside_wallet = get_mock_wallet()
    outside_synapse.dendrite.hotkey = outside_wallet.hotkey.ss58_address

    bl1, _ = await miner.blacklist(synapse)
    bl2, _ = await miner.blacklist(outside_synapse)

    assert not bl1
    if allow_non_registered:
        assert not bl2
    else:
        assert bl2


@pytest.mark.asyncio
async def test_miner_priority(setup_miner):
    miner = setup_miner
    synapse = Prove(index=0, poly=["123", "456"], alpha="789")
    synapse.dendrite.hotkey = miner.wallet.hotkey.ss58_address
    assert await miner.priority(synapse) > 0
