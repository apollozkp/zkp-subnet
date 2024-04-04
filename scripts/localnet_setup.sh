#!/bin/bash

# Create a coldkey for the owner role
NETWORK=${1:-127.0.0.1:9946}
WALLET=${2:-owner}
MINER=${3:-miner}
VALIDATOR=${4:-validator}
NETUID=${5:-1}

WALLETS_DIR=~/.bittensor/wallets

token_wallet() {
	cat ~/.bittensor/wallets/$1/coldkeypub.txt | grep -oP '"ss58Address": "\K[^"]+'
}

transfer_tokens() {
	btcli wallet transfer --subtensor.network $NETWORK --wallet.name $WALLET --dest $1 --amount $2 --no_prompt
}

register_wallet() {
	btcli subnet register --wallet.name $1 --netuid $NETUID --wallet.hotkey default --subtensor.chain_endpoint $NETWORK --no_prompt
}

stake() {
	btcli stake add --wallet.name $1 --wallet.hotkey default --subtensor.chain_endpoint $NETWORK --amount $2 --no_prompt
}

register() {
	# Give some time for the subtensor to start
	echo "LOCALNET_SETUP - Waiting for subnet to start"
	sleep 10

	echo "LOCALNET_SETUP - Registering subnet"
	btcli subnet create --wallet.name $WALLET --wallet.hotkey default --subtensor.chain_endpoint $NETWORK --no_prompt 2>&1
	# echo "LOCALNET_SETUP - Setting hyperparameters"
	# btcli sudo set --param min_burn --value 0 --netuid $NETUID --subtensor.chain_endpoint $NETWORK --wallet.name $WALLET --wallet.hotkey default --no_prompt 2>&1
	# btcli sudo set --param max_burn --value 0 --netuid $NETUID --subtensor.chain_endpoint $NETWORK --wallet.name $WALLET --wallet.hotkey default --no_prompt 2>&1
	echo "LOCALNET_SETUP - Hyperparameters set"
	btcli subnets hyperparameters --subtensor.chain_endpoint $NETWORK --netuid $NETUID 2>&1

	echo "LOCALNET_SETUP - Transferring tokens"
	# Transfer tokens to miner and validator coldkeys
	export BT_MINER_TOKEN_WALLET=$(token_wallet $MINER)
	export BT_VALIDATOR_TOKEN_WALLET=$(token_wallet $VALIDATOR)

	transfer_tokens $BT_MINER_TOKEN_WALLET 1000 2>&1
	transfer_tokens $BT_VALIDATOR_TOKEN_WALLET 10000 2>&1

	# Validator
	echo "LOCALNET_SETUP - Registering wallets"
	echo "LOCALNET_SETUP - Registering validator"
	register_wallet $VALIDATOR 2>&1
	echo "LOCALNET_SETUP - Staking"
	stake $VALIDATOR 9900 2>&1

	# Miner
	echo "LOCALNET_SETUP - Registering miner"
	register_wallet $MINER 2>&1

	# Ensure both the miner and validator keys are successfully registered.
	btcli subnets hyperparameters --subtensor.chain_endpoint $NETWORK --netuid $NETUID 2>&1
	btcli subnet list --subtensor.chain_endpoint $NETWORK 2>&1
	btcli wallet overview --wallet.name validator --subtensor.chain_endpoint $NETWORK --no_prompt 2>&1
	btcli wallet overview --wallet.name miner --subtensor.chain_endpoint $NETWORK --no_prompt 2>&1

	# Register to root network
	btcli root register --wallet.name validator --wallet.hotkey default --subtensor.chain_endpoint $NETWORK --no_prompt 2>&1
}

list_wallets() {
    # recursively list all the files in the ~/.bittensor/wallets directory
    # then print the path and the contents of the file
	echo "LOCALNET_SETUP - Wallets:"
    find $WALLETS_DIR -type f -exec sh -c 'echo "{}" && cat "{}" && echo' \;
}

setup_localnet() {
	echo "LOCALNET_SETUP - Setting up localnet, owner wallet: $WALLET, miner wallet: $MINER, validator wallet: $VALIDATOR"
	list_wallets

	if [ ! -d "$WALLETS_DIR/$WALLET" ]; then
		echo "LOCALNET_SETUP - $WALLETS_DIR/$WALLET does not exist"
		exit 1
	fi

	# Start registration first so that setup_and_run.sh can keep the box running
	register 2>&1 &

	echo "LOCALNET_SETUP - Creating setup_and_run.sh"
	echo "BUILD_BINARY=0 BT_DEFAULT_TOKEN_WALLET=$(cat ~/.bittensor/wallets/$WALLET/coldkeypub.txt | grep -oP '"ss58Address": "\K[^"]+') bash localnet.sh" >>/usr/local/bin/setup_and_run.sh
	chmod +x /usr/local/bin/setup_and_run.sh

	echo "LOCALNET_SETUP - Running setup_and_run.sh"
	bash setup_and_run.sh 2>&1

}

setup_localnet
