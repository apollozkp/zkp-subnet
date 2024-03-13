<div align="center">

# **Apollo Collaborate Zero-knowledge Proof Generation Subnet**
[![Discord Chat](https://img.shields.io/discord/308323056592486420.svg)](https://discord.gg/bittensor)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) 

[Website](http://apollozkp.com)

</div>

## Introduction

Bittensor subnets are a great way to provide open APIs aimed at outsourcing certain computational workloads, whether it be model inference, distributed learning or other highly specific compute. However, a key insight seems to be missing from most subnets out there today, which is that almost none of them seem to coordinate their miners to collaborate in order to achieve greater computational power; instead, they seem to often either perform computation redundantly, or miners are instead pitted in competition with each other, which may allow for a free market dynamic in the way of creating models, but severely limits the size of said models. We believe that Bittensor will only be fully leveraged if subnets begin thinking more deeply about collaborative mining, rather than redundant or competitive strategies. This is where Apollo comes in; a Bittensor subnet aimed at fruitfully combining compute power to achieve competitive results on the open market.

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

## License
This repository is licensed under the MIT License.
```text
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
```
