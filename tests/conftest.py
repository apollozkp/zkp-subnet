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

import os
import subprocess

import pytest

REPO_NAME = "fourier"
FOURIER_URL = "https://github.com/apollozkp/fourier"

TEST_SCALE = 6
TEST_MACHINES_SCALE = 2
TEST_SETUP_PATH = "test_setup.compressed"
TEST_PRECOMPUTE_PATH = "test_precompute.compressed"
TEST_BINARY = "test_prover"


@pytest.fixture(scope="session", autouse=True)
def compile_prover_lib():
    if os.path.exists(REPO_NAME):
        subprocess.check_call(f"rm -rf {REPO_NAME}", shell=True)

    subprocess.check_call(f"git clone {FOURIER_URL}", shell=True)

    base_path = os.getcwd()
    os.chdir("fourier")
    subprocess.check_call("git checkout move_fft", shell=True)
    subprocess.check_call("cargo build --release", shell=True)

    subprocess.check_call(
        f"mv target/release/fourier ../{TEST_BINARY}", shell=True
    )

    os.chdir(base_path)
    subprocess.check_call(f"chmod u+x ./{TEST_BINARY}", shell=True)
    subprocess.check_call(
        " ".join(
            [
                f"./{TEST_BINARY} setup",
                f"--setup-path {TEST_SETUP_PATH}",
                f"--precompute-path {TEST_PRECOMPUTE_PATH}",
                f"--scale {TEST_SCALE}",
                f"--machines-scale {TEST_MACHINES_SCALE}",
                "--generate-setup",
                "--generate-precompute",
                "--overwrite",
            ]
        ),
        # "./prover setup --setup-path setup --precompute-path precompute --scale 6 --machines-scale 4 --generate-setup --generate-precompute --overwrite",
        shell=True,
    )


@pytest.fixture(scope="session", autouse=True)
def cleanup_env(request):
    def cleanup():
        if os.path.exists(REPO_NAME):
            subprocess.check_call(f"rm -rf {REPO_NAME}", shell=True)
        for file in [TEST_BINARY, TEST_SETUP_PATH, TEST_PRECOMPUTE_PATH]:
            if os.path.exists(file):
                subprocess.check_call(f"rm {file}", shell=True)

        subprocess.check_call(f"pkill {TEST_BINARY}", shell=True)

    request.addfinalizer(cleanup)
