.PHONY: miner validator check-env clean miner-staging validator-staging miner-testnet validator-testnet

# Set RUST_LOG to debug to enable debug logging
RUST_LOG=debug

clean:
	-rm prover
	-rm setup_20_8.uncompressed
	-rm precompute_20_8.uncompressed
	-rm setup_24_8.uncompressed
	-rm precompute_24_8.uncompressed
	-rm .ensure-deps

.ensure-deps:
	sudo apt-get update && sudo apt-get install nodejs npm
	npm install -g pm2
	-. "$$HOME/.cargo/env" # source cargo just in case shell was never reloaded
	@command -v cargo >/dev/null 2>&1 || { \
		echo >&2 "Rust not installed. Installing..."; \
		curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y; \
	}
	@touch .ensure-deps

prover: .ensure-deps 
	rm -rf fourier # remove in case of a failed build
	git clone https://github.com/apollozkp/fourier
	cd fourier && . "$$HOME/.cargo/env" && cargo build --release && mv target/release/fourier ../prover
	rm -rf fourier

testnet-setup:
	if [ ! -f setup_20_8.uncompressed ]; then \
		curl -o setup_20_8.uncompressed https://apollozkp.s3.eu-north-1.amazonaws.com/setup_20_8.uncompressed; \
	fi

testnet-precompute:
	if [ ! -f precompute_20_8.uncompressed ]; then \
		curl -o precompute_20_8.uncompressed https://apollozkp.s3.eu-north-1.amazonaws.com/precompute_20_8.uncompressed; \
	fi

mainnet-setup:
	if [ ! -f setup_24_8.uncompressed ]; then \
		curl -o setup_24_8.uncompressed https://apollozkp.s3.eu-north-1.amazonaws.com/setup_24_8.uncompressed; \
	fi

mainnet-precompute:
	if [ ! -f precompute_24_8.uncompressed ]; then \
		curl -o precompute_24_8.uncompressed https://apollozkp.s3.eu-north-1.amazonaws.com/precompute_24_8.uncompressed; \
	fi

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
	pip install -r requirements.txt && pip install -e .

miner: mainnet-setup mainnet-precompute prover python-setup check-env RUST_LOG=$(RUST_LOG)
	pm2 start neurons/miner.py \
		--interpreter python3 \
		-- --netuid 10 \
		--wallet.name $(WALLET_NAME) \
		--wallet.hotkey $(HOTKEY_NAME) \
		--prover_path ./prover \
		--setup_path ./setup_24_8.uncompressed \
		--precompute_path ./precompute_24_8.uncompressed \
		--scale 24 \
		--machines_scale 8 \
		--uncompressed true

validator: mainnet-setup mainnet-precompute prover python-setup check-env 
	pm2 start neurons/validator.py \
		--interpreter python3 \
		-- --netuid 10 \
		--wallet.name $(WALLET_NAME) \
		--wallet.hotkey $(HOTKEY_NAME) \
		--prover_path ./prover \
		--setup_path ./setup_24_8.uncompressed \
		--precompute_path ./precompute_24_8.uncompressed \
		--scale 24 \
		--machines_scale 8 \
		--uncompressed true

miner-testnet: testnet-setup testnet-precompute prover python-setup check-env 
	RUST_LOG=debug && pm2 start neurons/miner.py \
		 --interpreter python3 \
		 -- --netuid 115 \
		 --subtensor.network test \
		 --wallet.name $(WALLET_NAME) \
		 --wallet.hotkey $(HOTKEY_NAME) \
		 --prover_path ./prover \
		 --setup_path ./setup_20_8.uncompressed \
		 --precompute_path ./precompute_20_8.uncompressed \
		 --scale 20 \
		 --machines_scale 8 \
		 --uncompressed true


validator-testnet: testnet-setup testnet-precompute prover python-setup check-env 
	RUST_LOG=debug && pm2 start neurons/validator.py \
		--interpreter python3 \
		-- --netuid 115 \
		--subtensor.network test \
		--wallet.name $(WALLET_NAME) \
		--wallet.hotkey $(HOTKEY_NAME) \
		--prover_path ./prover \
		--setup_path ./setup_20_8.uncompressed \
		--precompute_path ./precompute_20_8.uncompressed \
		--scale 20 \
		--machines_scale 8 \
		--uncompressed true

miner-staging: testnet-setup testnet-precompute prover python-setup check-env 
	RUST_LOG=debug && pm2 start neurons/miner.py \
		--interpreter python3 \
		-- --netuid 1 \
		--subtensor.chain_endpoint ws://127.0.0.1:9946 \
		--wallet.name $(WALLET_NAME) \
		--wallet.hotkey $(HOTKEY_NAME) \
		--prover_path ./prover \
		--setup_path ./setup_20_8.uncompressed \
		--precompute_path ./precompute_20_8.uncompressed \
		--scale 20 \
		--machines_scale 8 \
		--uncompressed true

validator-staging: testnet-setup testnet-precompute prover python-setup check-env 
	RUST_LOG=debug && pm2 start neurons/validator.py \
		--interpreter python3 \
		-- --netuid 1 \
		--subtensor.chain_endpoint ws://127.0.0.1:9946 \
		--wallet.name $(WALLET_NAME) \
		--wallet.hotkey $(HOTKEY_NAME) \
		--prover_path ./prover \
		--setup_path ./setup_20_8.uncompressed \
		--precompute_path ./precompute_20_8.uncompressed \
		--scale 20 \
		--machines_scale 8 \
		--uncompressed true

