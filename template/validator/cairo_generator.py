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
    return operations, previous_result_var  # Return all operations and the last result variable

def generate_main_function():
    num_operations = random.randint(10000, 50000)  # Decide the number of operations randomly
    operations, last_result_var = generate_random_operations_on_input(num_operations)

    operations_code = "\n    ".join(operations)
    main_function_template = f"""
func main() {{
    {operations_code}
    ret;
}}
"""
    return main_function_template

def generate_cairo_program():
    program = generate_main_function()
    return program

