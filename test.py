import bittensor as bt
import torch
from fourier import Client
import asyncio

from base.protocol import Prove

# Precomputed (small) polynomial, point and evaluation.
POLY = [
    "0cd70a3a63e25a07f3068874e8fdf9a5238b5b391b3b88d69aeb63815d83d6bf",
    "347600725caf9aa43827b6a61f44a28b94441178ee5b4bd76bc9875ec3e9b4f7",
    "689323bfea2caecbc9deb55057ad82939d62ce7087c5df26845bfb352b76bb43",
    "1475ce3ccbbe2534b6bda56880d5cabca486521a06be0b119a398f047f201135",
    "40480c2ba4f4d4d6951bf385eacdee2e62deaea98de2fbb6fa4b579203b66a70",
    "2fd31a457aa075a3be8c9ebd982f4544f477f0d7730a02a63807b19c9ba62e53",
]
X = "3970b257e06b2db2e040dee0d8be7242af39e009121b7527e2359c1adc7c35db"
Y = "0eacb75ad74a19f048530e1587df7c5e746f834f3c2e17dbbbba17df0fe91f3c"


# If no client is provided, the hardcoded values will be used.
# Otherwise, actual values will be generated.
def generate_challenge(client: Client, degree: int = 5) -> Prove:
    """
    Generate a challenge for the miners to solve. Consists of
    a random polynomial, a random point, and the evaluation of the
    polynomial at that point.
    """
    if not client:
        return Prove(poly=POLY, x=X, y=Y)
    # Generate a random polynomial.
    poly = client.random_poly(degree)
    x = client.random_point()
    y = client.evaluate(poly, x)
    return Prove(poly=poly, x=x, y=y)


# If no client is provided, returns True.
# Otherwise, verifies the response from the miners.
def verify_response(client: Client, response: Prove) -> bool:
    """
    Verify the response from the miners.
    """

    # Verify the proof.
    if not client:
        return True
    return client.verify_proof_single(
        response.proof, response.x, response.y, response.commitment
    )


async def main():
    LIVE_CLIENT = False
    NETUID = 10

    wallet = bt.wallet(name="validator", hotkey="default")
    dendrite = bt.dendrite(wallet=wallet)
    metagraph = bt.metagraph(netuid=NETUID)
    top_miner_uid = int(torch.argmax(metagraph.incentive))
    top_miner_axon = metagraph.axons[top_miner_uid]

    # Configure your client here.
    client = Client() if LIVE_CLIENT else None
    bt.logging.info(f"Client: {client} (if none, hardcoded values will be used)")

    timeout = 15
    bt.logging.info(
        f"Querying top miner {top_miner_uid} with timeout {timeout} seconds"
    )
    async with dendrite:
        response = await dendrite.forward(
            axons=[top_miner_axon],
            synapse=generate_challenge(client),
            deserialize=False,
            timeout=timeout,
        )

        responses = [(resp, resp.dendrite.process_time) for resp in response]
        bt.logging.info(f"Responses: {responses}")


if __name__ == "__main__":
    asyncio.run(main())
