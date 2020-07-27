from concurrent import futures
from loguru import logger
from typing import List

import math
import grpc
import random
import threading
import time

from opentensor import opentensor_pb2
from opentensor import opentensor_pb2_grpc as opentensor_grpc
import opentensor

class Metagraph(opentensor_grpc.MetagraphServicer):
    def __init__(self, bootstrap: List[str] = []):
        # Address-port gossip endpoints.
        self._peers = set()
        if len(bootstrap) > 0:
            self._peers.add(bootstrap)
        
        # List of graph synapses.
        self._synapses = {}
        self._heartbeat = {}

    def get_synapses(self, n: int) -> List[opentensor_pb2.Synapse]:
        """ Returns min(n, len(synapses)) synapse from the graph sorted by score."""
        # TODO (const) sort synapse array
        synapse_list = list(self._synapses.values())
        min_n = min(len(synapse_list), n)
        return synapse_list[:min_n]

    def get_peers(self, n: int) -> List[str]:
        """ Returns min(n, len(peers))"""
        peer_list = list(self._peers.values())
        min_n = min(len(peer_list), n)
        return peer_list[:min_n]
    
    def _sink(self, request: opentensor_pb2.SynapseBatch):
        for peer in request.peers:
            self.peers.add(peer)
        for synapse in request.synapses:
            self._synapses[synapse.synapse_key] = synapse
            self._heatbeat[synapse.synapse_key] = time.time()      

    def Gossip(self, request: opentensor_pb2.SynapseBatch, context):
        synapses = self._get_synapses(1000)
        peers = self._get_peers(10)
        self._sink(request)
        response = opentensor_pb2.SynapseBatch(peer=peers, synapses=synapses)
        return response
    
    def do_gossip(self):
        """ Sends ip query to random node in cache """
        if len(self._peers) == 0:
            return
        synapses = self._get_synapses(1000)
        peers = self._get_peers(10)
        metagraph_address = random.choice(list(self._peers))
        try:
            version = opentensor.PROTOCOL_VERSION
            channel = grpc.insecure_channel(realized_address)
            stub = opentensor_grpc.MetagraphStub(channel)
            request = opentensor_pb2.SynapseBatch(peers=peers,synapses=batch)
            response = stub.Gossip(request)
            self._sink(response)
        except:
            # Faulty peer.
            self._peers.remove(metagraph_address)
        
    def do_clean(self, ttl: int):
        """Cleans lingering metagraph elements
        Args:
            ttl (int): time to live.
        """
        now = time.time()
        for uid in list(self._synapses):
            if now - self._heartbeat[uid] > ttl:
                del self._synapses[uid]
                del self._heartbeat[uid]
                
    