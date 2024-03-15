.PHONY: ensure_deps miner validator prover

PYTHON_SETUP = pip install -r requirements.txt && python3 -m pip install -e .

ensure_deps:
	@command -v cargo >/dev/null 2>&1 || { \
		echo >&2 "Rust not installed. Installing..."; \
		curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y; \
		. "$HOME/.cargo/env"; \
	}

prover: ensure_deps
	git clone https://github.com/apollozkp/lambdaworks
	cd lambdaworks && cargo build --release && mv target/release/libcairo_platinum_prover.so ../
	rm -rf lambdaworks

# TODO: set netuid and subtensor
miner: prover
	$(PYTHON_SETUP)
	python neurons/miner.py --netuid 1 --wallet.name $(WALLET_NAME) --wallet.hotkey $(HOTKEY_NAME) --logging.debug # do this via pm2

# TODO: set netuid and subtensor
validator: prover
	$(PYTHON_SETUP)
	python neurons/validator.py --netuid 1 --wallet.name $(WALLET_NAME) --wallet.hotkey $(HOTKEY_NAME) --logging.debug # do this via pm2
