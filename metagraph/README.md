# Opentensor: Proxy service for Bittensor
[![Build status](https://circleci.com/gh/opentensor/bittensor_proxy.svg?style=shield)](https://circleci.com/gh/opentensor/bittensor_proxy)

## 
Connects together opentensor neurons.

## Run locally
1. Install python

```
# Install python dependencies
pip install -r requirments.txt

# Install protocol.
pip install -e .

# Run the server
python start_server.py

# Run the test client
python metagraph/client.py
```

## Run remote on Digital Ocean
1. Install Docker

1. Install Docker Machine

```
# Get API-token on Digital Ocean as $TOKEN
$ TOKEN=(your api token)

# Create a remote instance
$ docker-machine create --driver digitalocean --digitalocean-size s-4vcpu-8gb --digitalocean-access-token ${TOKEN} metagraph

# Switch to instance context
$ eval $(docker-machine env metagraph)

# Build the docker image.
$ docker build -t metagraph .

# Run the server
$ docker run -it -p 8888:8888 metagraph start_server.py

# Get instance ip address
$ ipaddress=$(eval docker-machine ip metagraph)

# Test the server 
python src/client.py --address=$ipaddress
```




