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
import json
import random
import bittensor as bt
from base.protocol import Trace
from utils.rust import make_proof
from utils.rust import make_trace_and_pub_inputs
from starkware.cairo.lang.cairo_constants import DEFAULT_PRIME
from starkware.cairo.lang.compiler.cairo_compile import compile_cairo

def generate_variable(id=None):
    return f"var_{random.randint(0, 999)}" if id is None else f"var_{id}"

def generate_number():
    return random.randint(1, 1000000)

def generate_arithmetic_operation(var1, var2, result_var):
    operations = ['+', '-', '*']
    operation = random.choice(operations)
    return f"let {result_var} = {var1} {operation} {var2};"

def generate_random_operations_on_input(num_operations):
    operations = []
    previous_result_var = generate_number()
    for i in range(num_operations):
        current_result_var = generate_variable(i)
        if i == 0:
            # First operation uses the public input directly
            operations.append(generate_arithmetic_operation(previous_result_var, str(generate_number()), current_result_var))
        else:
            # Subsequent operations use the result of the last operation
            next_var = generate_number() if random.choice([True, False]) else previous_result_var
            operations.append(generate_arithmetic_operation(previous_result_var, str(next_var), current_result_var))
        previous_result_var = current_result_var  # Update for next iteration
    return operations

def generate_main_function(minimum: int, maximum: int):
    num_operations = random.randint(minimum, maximum)
    operations = generate_random_operations_on_input(num_operations)

    operations_code = "\n    ".join(operations)
    main_function_template = f"""
func main() {{
    {operations_code}
    ret;
}}
"""
    return main_function_template

def generate_cairo_program(minimum: int, maximum: int):
    program = generate_main_function(minimum, maximum)
    bt.logging.debug("Random cairo program generated.")

    # Compile the program.
    assembled = compile_cairo(code=program, prime=DEFAULT_PRIME, add_start=True)
    bt.logging.debug("Random cairo program assembled.")

    # Parse to JSON for the Rust binary to interpret.
    program = assembled.Schema().dump(assembled)
    del program["compiler_version"]
    del program["main_scope"]
    program = json.dumps(program)

    return program

def generate_random_cairo_trace(minimum: int=10000, maximum: int=50000):
    # Generate a random cairo program.
    program = generate_cairo_program(minimum, maximum)

    # Generate trace and public inputs.
    main_trace, pub_inputs = make_trace_and_pub_inputs(program)
    bt.logging.debug("Trace and inputs created for random cairo program.")

    proof_bytes = make_proof(main_trace, pub_inputs)
    bt.logging.debug("Proof created for random cairo program.")

    main_trace = base64.b64encode(main_trace)
    pub_inputs = base64.b64encode(pub_inputs)

    # Combine all together into a Trace for the miner.
    return Trace(main_trace=main_trace, pub_inputs=pub_inputs), proof_bytes
