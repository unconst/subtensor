from metagraph import metagraph_pb2_grpc as proto_grpc
from metagraph import metagraph_pb2 as proto_pb2
from server import Metagraph

import argparse
import grpc

from concurrent import futures

def create_default_hparams():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--wait_clean',
        default=100,
        type=int,
        help="Time between stale entry cleaning. Default=100")
    hparams = parser.parse_args()
    return hparams

def create_server(config):
    address = "[::]:8888"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    metagraph_server = Metagraph(config)
    proto_grpc.add_MetagraphServicer_to_server(metagraph_server, server)
    server.add_insecure_port(address)
    return server, metagraph_server

def test_create():
    config = create_default_hparams()
    server, _ = create_server(config)
    server.start()
    server.stop(0)
    del server

def test_clean():
    config = create_default_hparams()
    server, metagraph_server = create_server(config)
    metagraph_server.clean()
    del server

