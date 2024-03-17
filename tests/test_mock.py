import pytest
import asyncio
import bittensor as bt
from base.mock import MockMetagraph, MockSubtensor
from base.protocol import Trace


@pytest.mark.parametrize("netuid", [2, 3, 4])
@pytest.mark.parametrize("n", [2, 4, 8, 16, 32, 64])
@pytest.mark.parametrize("wallet", [bt.MockWallet(), None])
def test_mock_subtensor(netuid, n, wallet):
    subtensor = MockSubtensor(netuid=netuid, n=n, wallet=wallet)
    neurons = subtensor.neurons(netuid=netuid)
    # Check netuid
    assert subtensor.subnet_exists(netuid)
    # Check network
    assert subtensor.network == "mock"
    assert subtensor.chain_endpoint == "mock_endpoint"
    # Check number of neurons
    assert len(neurons) == (n + 1 if wallet is not None else n)
    # Check wallet
    if wallet is not None:
        assert subtensor.is_hotkey_registered(
            netuid=netuid, hotkey_ss58=wallet.hotkey.ss58_address
        )

    for neuron in neurons:
        assert type(neuron) == bt.NeuronInfo
        assert subtensor.is_hotkey_registered(
            netuid=netuid, hotkey_ss58=neuron.hotkey
        )

    subtensor.reset()

@pytest.mark.parametrize("n", [16, 32, 64])
def test_mock_metagraph(n):
    mock_subtensor = MockSubtensor(netuid=5, n=n)
    mock_metagraph = MockMetagraph(netuid=5, subtensor=mock_subtensor)
    # Check axons
    axons = mock_metagraph.axons
    assert len(axons) == n
    # Check ip and port
    for axon in axons:
        assert type(axon) == bt.AxonInfo
        assert axon.ip == "127.0.0.0"
        assert axon.port == 8091

    mock_subtensor.reset()
