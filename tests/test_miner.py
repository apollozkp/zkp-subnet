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

TEST_POLY = [
    "6945DC5C4FF4DAC8A7278C9B8F0D4613320CF87FF947F21AC9BF42327EC19448",
    "68E40C088D827BCCE02CEF34BDC8C12BB025FBEA047BC6C00C0C8C5C925B7FAF",
    "67281FAC164E9348B80693BA30D5D4E311DE5878EB3D20E34A58507B484B243C",
    "5F7C377DAE6B9D9ABAD75DC15E4FFF9FE7520D1F85224C95F485F44978154C5A",
    "2D85C376A440B6E25C3F7C11559B6A27684023F36C3D7A0ACD7E7D019DE399C7",
    "4A6FB95F0241B3583771E799120C87AAE3C843ECDB50A38254A92E198968922F",
    "1005079F96EC412A719FE2E9FA67D421D98FB4DEC4181459E59430F5D502BD2A",
    "64960B8692062DCB01C0FFBAC569478A89AD880ED3C9DF710BED5CE75F484693",
    "03C2882155A447642BD21FB1CF2553F80955713F09BBBBD9724E2CBFD8B19D41",
    "0AB07FECB59EE3435F6129FCD602CB519E56D7B426941633E37A3B676A24830F",
    "12FA5861459EFFBAE654827D98BFDFEA5545DDF8BB9628579463DA21F17462B5",
    "6A6296A0376D807530DB09DC8BB069FFDEC3D7541497B82C722A199D6B7C5B06",
    "153D2C81B54D7E1C3E83EA61C7F66FD88155F1713EE581E2BE8438CA9FEE1A02",
    "216BCCC4AE97FE3E1D4B21C375C46140FA153E7868201A43480889047ACD0C2D",
    "381BD4FE924EB10E08F2A227D3DB2083AA0E5A1F661CD3C702C4B8A9385E7839",
    "723A7640FD7E65473131563AB5514916AC861C2695CE6513E5061E597E5E1A81",
]

TEST_POINT = "456006fff56412d329d527901d02877a581a89cfa677ca963eb9d680766234cc"
TEST_EVAL = "29732a1e0e074ab05ee6a9e57794c5ad1965b98b6c8c6ecde96ac776ea06ff5b"

TEST_SYNAPSE = Prove(poly=TEST_POLY, x=TEST_POINT, y=TEST_EVAL)


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
def test_miner_forward(setup_miner, n):
    miner = setup_miner

    with miner.client.commit(TEST_SYNAPSE.poly) as resp:
        assert resp.status_code == 200
        commitment = resp.json().get("result", {}).get("commitment")

    with miner.client.open(TEST_SYNAPSE.poly, TEST_SYNAPSE.x) as resp:
        assert resp.status_code == 200
        proof = resp.json().get("result", {}).get("proof")

    with miner.client.verify(proof, TEST_SYNAPSE.x, TEST_SYNAPSE.y, commitment) as resp:
        assert resp.status_code == 200
        assert resp.json().get("result", {}).get("valid")


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
    synapse = Prove(poly=poly)
    synapse.dendrite.hotkey = miner.wallet.hotkey.ss58_address

    outside_synapse = Prove(poly=poly)
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
    synapse = Prove(poly=["a"])
    synapse.dendrite.hotkey = miner.wallet.hotkey.ss58_address
    assert await miner.priority(synapse) > 0
