ARG BASE_IMAGE=ubuntu:20.04
# Use the official ubuntu image as a parent image
FROM $BASE_IMAGE as builder

# Avoid warnings by switching to noninteractive
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Install dependencies
RUN apt-get update && apt-get install -y pkg-config make build-essential git clang curl libssl-dev llvm libudev-dev protobuf-compiler tmux libgmp-dev python3-pip 

# Install rust and cargo
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Clone subtensor and enter the directory
RUN git clone https://github.com/opentensor/subtensor.git && cd subtensor && git checkout main && git pull && cd ..

WORKDIR /subtensor

# Update to the nightly version of rust
RUN /subtensor/scripts/init.sh

WORKDIR /

# TODO: fix the fourier package so this is not necessary
# Pull the fourier package
RUN git clone https://github.com/apollozkp/fourier.git
WORKDIR /fourier
RUN cargo build --release

# Build subtensor
WORKDIR /subtensor
RUN cargo build --release --features pow-faucet

##########################
# Create the child image #
##########################
FROM $BASE_IMAGE as localnet

# Avoid warnings by switching to noninteractive
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Install dependencies
RUN apt-get update && apt-get install -y pkg-config make build-essential git clang curl libssl-dev llvm libudev-dev protobuf-compiler libgmp-dev python3 python3-pip
RUN apt-get install -y netcat

# Install rust and cargo
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# TODO: fix the fourier package so this is not necessary
RUN mkdir /target
RUN mkdir /target/release

# Copy the subtensor binary and localnet script
COPY --from=builder /subtensor/target/release/node-subtensor /usr/local/bin/
COPY --from=builder /subtensor/scripts/localnet.sh /usr/local/bin/

# Copy zkp-subnet
# TODO: fix the fourier package so this is not necessary
COPY --from=builder /fourier/target/release/fourier /target/release/fourier

# Install python dependencies
COPY /requirements.txt /
COPY /base /base
COPY /api /api
COPY /neurons /neurons
COPY /utils /utils
COPY /setup.py /
COPY /README.md /

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -e .
RUN python3 -m pip install -r /requirements.txt
# RUN python3 -m pip install --upgrade bittensor

# Setup wallets
ARG WALLET=owner
ARG MINER=miner
ARG VALIDATOR=validator

RUN mkdir -p /root/.bittensor
RUN btcli wallet new_coldkey --wallet.name $WALLET --no_password --no_prompt
RUN btcli wallet new_coldkey --wallet.name $MINER --no_password --no_prompt
RUN btcli wallet new_hotkey --wallet.name $MINER --wallet.hotkey default --no_prompt
RUN btcli wallet new_coldkey --wallet.name $VALIDATOR --no_password --no_prompt
RUN btcli wallet new_hotkey --wallet.name $VALIDATOR --wallet.hotkey default --no_prompt


# Copy setup scripts
COPY /scripts/localnet_setup.sh /usr/local/bin/
COPY /scripts/localnet.sh /usr/local/bin/
COPY /scripts/miner_setup.sh /usr/local/bin/
COPY /scripts/validator_setup.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/localnet_setup.sh
RUN chmod +x /usr/local/bin/localnet.sh
RUN chmod +x /usr/local/bin/miner_setup.sh
RUN chmod +x /usr/local/bin/validator_setup.sh

# Just here to refresh build cache
RUN mkdir /garbo
COPY /scripts /garbo

