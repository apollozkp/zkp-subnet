NETWORK=${1:-127.0.0.1:9946}
WALLET=${2:-owner}
MINER=${3:-miner}
VALIDATOR=${4:-validator}
NETUID=${5:-1}

validator-staging() {
    IFS=: read -r IP PORT <<< "$NETWORK"
    while ! nc -z $IP $PORT; do
        echo "VALIDATOR_SETUP - Waiting for subnet to start"
        sleep 5
    done
	echo "VALIDATOR_SETUP - Starting validator"
    # restart script if it fails
    while true; do
	    python3 neurons/validator.py --netuid $NETUID --subtensor.chain_endpoint $NETWORK --wallet.name $VALIDATOR --wallet.hotkey default --logging.debug
        sleep 15
    done
}

validator-staging 2>&1
