<div align="center">

# **Apollo Collaborative Zero-knowledge Proof Generation Subnet**
[![Discord Chat](https://img.shields.io/discord/308323056592486420.svg)](https://discord.gg/bittensor)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) 

[Website](https://apollozkp.com)

</div>

## Introduction

Bittensor subnets are a great way to provide open APIs aimed at outsourcing certain computational workloads, whether it be model inference, distributed learning or other highly specific compute. However, a key insight seems to be missing from most subnets out there today, which is that almost none of them seem to coordinate their miners to collaborate in order to achieve greater computational power; instead, they seem to often either perform computation redundantly, or miners are instead pitted in competition with each other, which may allow for a free market dynamic in the way of creating models, but severely limits the size of said models. We believe that Bittensor will only be fully leveraged if subnets begin thinking more deeply about collaborative mining, rather than redundant or competitive strategies. This is where Apollo comes in; a Bittensor subnet aimed at fruitfully combining compute power to achieve competitive results on the open market.

## Roadmap

- [ ] Deploy v0 on Bittensor testnet | In progress...
- [ ] Deploy v0 on Bittensor mainnet
- [ ] Implement and deploy vanilla-PLONK style constraint aggregation
- [ ] Build payment infrastructure to fully open a public API for proof generation with payouts to miners and validators
- [ ] Extend constraint aggregation support to any type of circuit (KZG only)
- [ ] Explore segmented lookup tables in constraint aggregation work
- [ ] Perform further research into distributing work for other commitment schemes
- [ ] Explore other fruitful opportunities for miner collaboration outside of ZKP generation

## Hardware requirements

For this version 0, it is advised that validators run slightly stronger hardware than miners do. This is needed due to the computational cost of converting Cairo programs to a set of constraints which a miner can then prove to signal his capability.

### Validator requirements

- At least 8 vCPUs
- At least 16 GB RAM (DDR4 or higher)
- 200 GB storage

### Miner requirements

- At least 4 vCPUs
- At least 16 GB RAM (DDR4 or higher)
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

TODO: get network uids so that we can instruct users on how to deploy

Then, ensure you have the subnet code on your machine.

> NOTE: THE CODE ALWAYS ASSUMES THAT THE REPOSITORY IS CLONED IN THE `/root` DIRECTORY. FAILURE TO DO SO WILL CAUSE BREAKAGE OF THE MINER AND VALIDATOR NEURONS.

```bash
cd /root
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
