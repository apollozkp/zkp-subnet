# The MIT License (MIT)
# Copyright © 2024 Apollo

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMI TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import pytest
from starkware.cairo.lang.cairo_constants import DEFAULT_PRIME

from utils.cairo_generator import (
    generate_arithmetic_operation,
    generate_cairo_program,
    generate_main_function,
    generate_random_operations_on_input,
    generate_variable,
)


@pytest.mark.parametrize("n", [8, 12, 7432])
def test_generate_variable(n):
    var = generate_variable(n)
    assert var == f"var_{n}"


@pytest.mark.parametrize(
    "var1,var2,result_var",
    [
        ("var_10", "var_11", "result"),
        ("var_2", "var_1", "result"),
        ("var_18", "var_82734", "result"),
        ("var_12", "var_a", "result"),
        ("var_83", "hi", "result"),
        ("var_77", "var_738", "result"),
        ("v", "var_", "result"),
    ],
)
def test_generate_arithmetic_operation(var1, var2, result_var):
    op = generate_arithmetic_operation(var1, var2, result_var)
    assert "+" in op or "-" in op or "*" in op
    assert f"let {result_var} = " in op
    assert f"{var1}" in op
    assert f"{var2}" in op
    assert op.endswith(";")


@pytest.mark.parametrize("num_operations", [724, 4123, 10273])
def test_generate_random_operations_on_input(num_operations):
    ops = generate_random_operations_on_input(num_operations)
    assert len(ops) == num_operations

    i = 0
    for op in ops:
        assert f"var_{i}" in op
        i = i + 1

        if i != 0:
            assert f"var_{i-1}" in op


@pytest.mark.parametrize("n", [10, 100, 1000])
def test_generate_main_function(n):
    main = generate_main_function(n, n)
    lines = main.splitlines()
    assert len(lines) == n + 4
    assert main.startswith("\nfunc main() {\n")
    assert main.endswith("ret;\n}\n")


@pytest.mark.parametrize("n", [10, 100, 1000])
def test_generate_cairo_program(n):
    program = generate_cairo_program(n, n)

    # ensure garbage is deleted
    assert "compiler_version" not in program
    assert "main_scope" not in program

    # ensure all needed fields exist for the rust binary to decode it
    assert "prime" in program
    assert (
        f"{hex(DEFAULT_PRIME)}" in program
    )  # we only work with the default prime for now
    assert "builtins" in program
    assert "data" in program
    assert "identifiers" in program
    assert "hints" in program
    assert "reference_manager" in program
    assert "attributes" in program
    assert "debug_info" in program
