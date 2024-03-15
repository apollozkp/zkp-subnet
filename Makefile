.PHONY: miner validator check-env clean miner-staging validator-staging miner-testnet validator-testnet

clean:
	rm prover

ensure-deps:
	sudo apt-get update && sudo apt-get install libgmp-dev # we need gmp for cairo lib
	. "$$HOME/.cargo/env" # source cargo just in case shell was never reloaded
	@command -v cargo >/dev/null 2>&1 || { \
		echo >&2 "Rust not installed. Installing..."; \
		curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y; \
	}

prover: ensure-deps 
	rm -rf lambdaworks # remove in case of a failed build
	git clone https://github.com/apollozkp/lambdaworks
	cd lambdaworks && . "$$HOME/.cargo/env" && cargo build --release && mv target/release/libcairo_platinum_prover.so ../prover
	rm -rf lambdaworks

check-env:
	@if [ -z "$${WALLET_NAME}" ]; then \
		echo "WALLET_NAME is not set" >&2; \
		exit 1; \
	fi
	@if [ -z "$${HOTKEY_NAME}" ]; then \
		echo "HOTKEY_NAME is not set" >&2; \
		exit 1; \
	fi

python-setup:
	pip install -r requirements.txt && python3 -m pip install -e .

# TODO: set netuid and subtensor
miner: prover python-setup check-env
	python3 neurons/miner.py --netuid 1 --wallet.name $(WALLET_NAME) --wallet.hotkey $(HOTKEY_NAME) --logging.debug # do this via pm2

# TODO: set netuid and subtensor
validator: prover python-setup check-env
	python3 neurons/validator.py --netuid 1 --wallet.name $(WALLET_NAME) --wallet.hotkey $(HOTKEY_NAME) --logging.debug # do this via pm2

# TODO: set netuid and subtensor
miner-testnet: prover python-setup check-env
	python3 neurons/miner.py --netuid 1 --wallet.name $(WALLET_NAME) --wallet.hotkey $(HOTKEY_NAME) --logging.debug # do this via pm2

# TODO: set netuid and subtensor
validator-testnet: prover python-setup check-env
	python3 neurons/validator.py --netuid 1 --wallet.name $(WALLET_NAME) --wallet.hotkey $(HOTKEY_NAME) --logging.debug # do this via pm2

miner-staging: prover python-setup check-env
	python3 neurons/miner.py --netuid 1 --subtensor.chain_endpoint ws://127.0.0.1:9946 --wallet.name $(WALLET_NAME) --wallet.hotkey $(HOTKEY_NAME) --logging.debug # do this via pm2

validator-staging: prover python-setup check-env
	python3 neurons/validator.py --netuid 1 --subtensor.chain_endpoint ws://127.0.0.1:9946 --wallet.name $(WALLET_NAME) --wallet.hotkey $(HOTKEY_NAME) --logging.debug # do this via pm2
