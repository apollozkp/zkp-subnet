NETWORK=${1:-127.0.0.1:9946}
WALLET=${2:-owner}
MINER=${3:-miner}
VALIDATOR=${4:-validator}
NETUID=${5:-1}

miner-staging() {
    IFS=: read -r IP PORT <<< "$NETWORK"
    while ! nc -z $IP $PORT; do
        echo "MINER_SETUP - Waiting for subnet to start"
        sleep 5
    done
	echo "MINER_SETUP - Starting miner"
	
    # restart script if it fails
    while true; do
        python3 neurons/miner.py --netuid $NETUID --subtensor.chain_endpoint $NETWORK --wallet.name $MINER --wallet.hotkey default --logging.debug
        sleep 15
    done
}

miner-staging 2>&1 
