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

LAMBDAWORKS_URL = "https://github.com/apollozkp/lambdaworks"

import pytest
import subprocess
import os

@pytest.fixture(scope="session", autouse=True)
def compile_prover_lib():
    if os.path.exists("lambdaworks"):
        subprocess.check_call("rm -rf lambdaworks", shell=True)

    subprocess.check_call(f"git clone {LAMBDAWORKS_URL}", shell=True)

    os.chdir("lambdaworks")
    subprocess.check_call("cargo build --release", shell=True)

    compiled_path = os.path.join("lambdaworks", "target/release/libcairo_platinum_prover.so")
    os.chdir("..")
    yield compiled_path

@pytest.fixture(scope="session", autouse=True)
def cleanup_env(request):
    def cleanup():
        if os.path.exists("lambdaworks"):
            subprocess.check_call("rm -rf lambdaworks", shell=True)

    request.addfinalizer(cleanup)
