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

import random
import io
import json
import base64
import bittensor as bt
from template.protocol import Trace
from template.validator.reward import get_rewards
from template.validator.cairo_generator import generate_cairo_program
from template.utils.uids import get_random_uids
from template.utils.rust import make_proof
from template.utils.rust import make_trace_and_pub_inputs
from starkware.cairo.lang.cairo_constants import DEFAULT_PRIME
from starkware.cairo.lang.compiler.cairo_compile import compile_cairo

def generate_random_cairo_trace(minimum: int=10000, maximum: int=50000):
    # Generate a random cairo program.
    program = generate_cairo_program(minimum, maximum)
    bt.logging.debug("Random cairo program generated.")

    # Compile the program.
    assembled = compile_cairo(code=program, prime=DEFAULT_PRIME, add_start=True)
    bt.logging.debug("Random cairo program assembled.")

    # Parse to JSON for the Rust binary to interpret.
    program = assembled.Schema().dump(assembled)
    del program["compiler_version"]
    del program["main_scope"]
    program = json.dumps(program)

    # Generate trace and public inputs.
    main_trace, pub_inputs = make_trace_and_pub_inputs(program)
    bt.logging.debug("Trace and inputs created for random cairo program.")

    proof_bytes = make_proof(main_trace, pub_inputs)
    bt.logging.debug("Proof created for random cairo program.")

    main_trace = base64.b64encode(main_trace)
    pub_inputs = base64.b64encode(pub_inputs)

    # Combine all together into a Trace for the miner.
    return Trace(main_trace=main_trace, pub_inputs=pub_inputs), proof_bytes

async def forward(self):
    """
    The forward function is called by the validator every time step.

    It is responsible for querying the network and scoring the responses.

    Args:
        self (:obj:`bittensor.neuron.Neuron`): The neuron object which contains all the necessary state for the validator.

    """
    miner_uids = get_random_uids(self, k=min(self.config.neuron.sample_size, self.metagraph.n.item()))
    trace, proof_bytes = generate_random_cairo_trace()

    # For completeness, validators also need to generate proofs to ensure that miners are generating
    # proofs of the given trace, rather than just creating any random garbage proof that will pass
    # verification.

    responses = await self.dendrite(
        axons=[self.metagraph.axons[uid] for uid in miner_uids],
        synapse=trace, # send in the execution trace
        deserialize=False, # bogus responses shouldn't kill the validation flow
        timeout=10,
    )

    def try_deserialize(item: Trace):
        try:
            return item.deserialize()
        except:
            return bytes()

    responses = [try_deserialize(item) for item in responses]

    # Log the results for monitoring purposes.
    bt.logging.info(f"Received responses: {responses}")

    # Adjust the scores based on responses from miners.
    rewards = get_rewards(self, proof_bytes, responses)

    bt.logging.info(f"Scored responses: {rewards}")
    # Update the scores based on the rewards. You may want to define your own update_scores function for custom behavior.
    self.update_scores(rewards, miner_uids)
