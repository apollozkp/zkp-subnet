<div align="center">

# **Apollo Collaborative Zero-knowledge Proof Generation Subnet**
[![Discord Chat](https://img.shields.io/discord/308323056592486420.svg)](https://discord.com/channels/799672011265015819/1222672871092912262)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) 
![example workflow](https://github.com/apollozkp/zkp-subnet/actions/workflows/ci.yml/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/apollozkp/zkp-subnet/badge.svg?branch=main)](https://coveralls.io/github/apollozkp/zkp-subnet?branch=main)

[Website](https://apollozkp.com)

</div>

## Introduction

Bittensor subnets are a great way to provide open APIs aimed at outsourcing certain computational workloads, whether it be model inference, distributed learning or other highly specific compute. However, a key ingredient to create extra valuable APIs is simply the leveraging of collaborative computation, rather than competitive computation. We believe that Bittensor will only be fully leveraged if subnets begin thinking more deeply about collaborative mining in tandem with the current approach. This is why we are building Apollo, and our first subnet will be a great example of the potential impact we can make; which is aimed at fruitfully combining compute power to achieve competitive results on the open market.

Our first objective - to create a publicly available, massively scalable, concretely competitive and extremely cost-effective zero-knowledge proof generation cluster, by leveraging the work of [Pianist](https://eprint.iacr.org/2023/1271.pdf).

Our aim with this subnet is to provide a public API which can easily undercut costs of bespoke GPU cluster solutions, and to become the go-to solution for many blockchain protocols and applications that are live today which leverage the magic of zero-knowledge proofs.

## Features

- Out of the box working implementation for good-enough proving speed (CPU only for now)
- One-command setup, with easy process management through `pm2`
- Context-dependent validation scoring (always at least one winner)
- Fully randomized validation inputs, keeping mining fair

### To be added

- Out of the box CUDA implementation for simpler competition
- Tutorials and tooling to create your own proving clusters, or using your own specialized hardware
- An open, permissionless, market-driven API which opens up a powerful proving cluster to the public, allowing for ZK usecases before considered infeasible, such as provable inference

## Roadmap

- [x] Deploy v0 on Bittensor testnet
- [ ] Deploy v0 on Bittensor mainnet | In progress...
- [ ] Implement and deploy vanilla-PLONK style constraint aggregation
- [ ] Build payment infrastructure to fully open a public API for proof generation with payouts to miners and validators
- [ ] Extend constraint aggregation support to any type of circuit (KZG only)
- [ ] Explore segmented lookup tables in constraint aggregation work
- [ ] Perform further research into distributing work for other commitment schemes
- [ ] Explore other fruitful opportunities for miner collaboration outside of ZKP generation

## Hardware requirements

### Validator requirements

- Ubuntu 22.04
- At least 8 physical cores @ 3.0 GHz
- At least 64 GB RAM (DDR4 or higher)
- 200 GB storage

### Miner requirements

- Ubuntu 22.04
- At least 8 physical cores @ 3.0 GHz
- At least 64 GB RAM (DDR4 or higher)
- 200 GB storage

## Getting started

Very minimally, you will want to at least have:

- Python 3.8 or higher
- [Bittensor CLI](https://github.com/opentensor/bittensor/blob/master/README.md#install) installed

Next, you will want to set up a coldkey and hotkey, if you are planning on mining or validating on the Apollo subnet.

```bash
btcli wallet new_coldkey --wallet.name <your_wallet_name>
btcli wallet new_hotkey --wallet.name <your_wallet_name> --wallet.hotkey <your_hotkey_name>
```

Be sure to replace `<your_wallet_name>` and `<your_hotkey_name>` with names of your choosing.

Then, ensure you have the subnet code on your machine.

```bash
git clone https://github.com/apollozkp/zkp-subnet.git
cd zkp-subnet
```

Finally, to start a miner, run:

```bash
make miner WALLET_NAME=<your_wallet_name> HOTKEY_NAME=<your_hotkey_name>
```

where `<your_wallet_name>` is the name of your wallet, and `<your_hotkey_name>` is the name of your hotkey.

To start a validator, run:

```bash
make validator WALLET_NAME=<your_wallet_name> HOTKEY_NAME=<your_hotkey_name>
```

where `<your_wallet_name>` is the name of your wallet, and `<your_hotkey_name>` is the name of your hotkey.

The command starts a `pm2` process which ensures that the miner or validator will continue running, even if you log out of your server session. To check the logs, simply type:

```bash
pm2 logs
```

to get a look at what's happening.

### Updating the miner/validator

If a new update has been released, you may update your miner or validator by running

```bash
pm2 stop <miner/validator>
```

choosing `miner` or `validator` depending on what you're running. Then, you can use

```bash
git pull
```

to update the codebase. Finally, you can run the same `make` command as you did before to restart your miner or validator, and use `pm2 logs` to observe the output.

### Validators only

When registered and running, you can increase your stake to the subnet by running:

```bash
btcli stake add --wallet.name validator --wallet.hotkey default
```

## Contributing

Please see the [contribution guidelines](./contrib/CONTRIBUTING.md) for details.

## License
This repository is licensed under the MIT License.
```text
The MIT License (MIT)
Copyright © 2024 Apollo

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the “Software”), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of
the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
```

The repository also contains code licensed by Yuma Rao under the MIT License.

```text
The MIT License (MIT)
Copyright © 2023 Yuma Rao

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the “Software”), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of
the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
```
