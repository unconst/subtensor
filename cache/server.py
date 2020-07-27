from opentensor import opentensor_pb2_grpc as opentensor_grpc
from opentensor import opentensor_pb2 

from loguru import logger

import copy
import math
import numpy
import json
import time

class Proxy(opentensor_grpc.MetagraphProxyServicer):

    def __init__(self):
        self._neurons = {}
        self._heartbeat = {}

    def refresh(self):
        self._clean()
        json_obj = self._toJson()
        with open('graph.json', 'w') as outfile:
            json.dump(json_obj, outfile)
        logger.info(json_obj)

    def _clean(self):
        for n in list(self._neurons.values()):
            delta = time.time() - self._heartbeat[n.public_key]
            if delta > 30:
                self._remove(n)

    def _toJson(self):
        json_obj = {'nodes':[], 'links':[]}
        lingering = []
        for n in self._neurons.values():
            n_entry = {'id': n.public_key}
            json_obj['nodes'].append(n_entry)
            for node in n.nodes:
                json_obj['nodes'].append({'id': node.identity})
                json_obj['links'].append({ 
                    'source': node.identity, 
                    'target': n.public_key,
                    'value': 1.0
                })
            for w in n.weights:
                if w.target in self._neurons:
                    json_obj['links'].append({
                        'source': n.public_key,
                        'target': w.target,
                        'value': w.value
                    })
        return json_obj
    
    def _add(self, neuron):
        logger.info('add: {}', neuron)
        self._neurons[neuron.public_key] = neuron
    
    def _remove(self, neuron):
        logger.info('remove:{}', neuron)
        if neuron.public_key in self._neurons:
            del self._neurons[neuron.public_key]

    def Subscribe(self, neuron, context):
        self._add(neuron)
        self._heartbeat[neuron.public_key] = time.time()
        return opentensor_pb2.ACK()
    
    def Unsubscribe(self, neuron, context):
        self._remove(neuron)
        return opentensor_pb2.ACK()

    def GetMetagraph(self, request, context):
        return opentensor_pb2.Metagraph(neurons=self._neurons.values())  


'''
        self.heartbeat = {}
        self.start_time = None
        self.total_supply = 0.0

        # Incentive mechanism params.
        self.W = {}
        self.R = {}
        self.I = {}
        self.S = {}

    def SetWeights(self, request, context):
        logger.info('set weights {}', request)
        key = request.publickey
        ids = list(request.ids)
        in_weights = list(request.weights)
        self.W[key] = {}
        for i, iden in enumerate(ids):
            self.W[key][iden] = in_weights[i]
        response = proto_pb2.SetWeightsResponse()
        return response

    def Subscribe(self, request, context):
        if self.start_time == None:
            self.start_time = time.time()
        logger.info('subscribe {}', str(request))
        self.peers[request.publickey] = request
        self.heartbeat[request.publickey] = time.time()
        if request.publickey not in self.W:
            self.W[request.publickey] = {}
        for w in request.weights:
            self.W[w.source][w.target] = w.value
        if request.publickey not in self.R:
            self.R[request.publickey] = 0
        if request.publickey not in self.I:
            self.I[request.publickey] = 0
        if request.publickey not in self.S:
            self.S[request.publickey] = 0
        response = proto_pb2.SubscribeResponse()
        return response

    def Unsubscribe(self, request, context):
        logger.info('unsubscribe {}', str(request))
        self.remove(request.publickey)
        response = proto_pb2.UnsubscribeResponse()
        return response
    
    def GetMetagraph(self, request, context): 
        neurons = []
        for key in self.peers:
            neurons.append(
                    proto_pb2.Neuron(
                        version=1.0,
                        publickey=key,
                        heartbeat=self.heartbeat[key],
                        address=self.peers[key].address,
                        port=self.peers[key].port,
                        rank=self.R[key],
                        incentive=self.I[key],
                        stake=self.S[key]))
        weights = []
        for key_i in self.W:
            for key_j in self.W[key_i]:
                weights.append(
                    proto_pb2.Weight(
                        version=1.0,
                        source=key_i,
                        target=key_j))

        response = proto_pb2.MetagraphResponse(
                        neurons=neurons,
                        weights=weights)
        return response

    def remove(self, key):
        self.heartbeat.pop(key, None)
        self.peers.pop(key, None)
        self.W.pop(key, None)
        self.R.pop(key, None)
        self.I.pop(key, None)
        self.S.pop(key, None)

    def refresh(self):
        try:
            self.clean()
            self.computeR()
            self.computeI()
            self.computeS()
            self.logtostd()
            self.tofile()
        except Exception as e:
            logger.info('Exception while trying to refresh: {}', e)


    def clean(self):
        for key in list(self.peers):
            last = self.heartbeat[key]
            now = time.time()
            if (now - last) > self.config.time_to_live:
                logger.info('cleaned {}', self.peers[key])
                self.remove_peer(key)
    
    def computeR(self):
        self.R = {}
        for key in self.peers:
            self.R[key] = 0.0
        for key_i in self.W:
            for key_j in self.W[key_i]:
                if key_j not in self.R:
                    self.R[key_j] = 0.0
                self.R[key_j] += self.W[key_i][key_j]

    def computeI(self):
        self.I = {}
        denom = 0
        for r_i in self.R.values():
            denom += math.exp(r_i)
        if denom == 0:
            denom = 1
        for key in self.R:
            self.I[key] = math.exp(self.R[key]) / denom

    def supply_at(self, x):
        x = x/(60 * 60 * 24)
        a = math.log(x + 730/3) / math.log(math.exp(1)) 
        b = math.log(730/3) / math.log(math.exp(1))
        return 6000000 * (a - b)
         
    def computeS(self):
        if not self.start_time:
            return
        elapsed = time.time() - self.start_time
        to_emit = self.supply_at(elapsed) - self.total_supply
        for key in self.I:
            if key not in self.S:
                self.S[key] = 0.0
            self.S[key] = self.S[key] + self.I[key] * to_emit
        self.total_supply = sum(self.S.values())

    def tofile(self):
        data = {}
        index = 0
        peer_index = {}
        data['nodes'] = []
        for key in self.peers:
            values = self.peers[key]
            data['nodes'].append({
                'id': int(index),
                'name': values.publickey,
                'R': self.R[key],
                'I': self.I[key],
                'S': self.S[key]
            })
            peer_index[key] = index
            index += 1

        for key_i in self.W:
            for key_j in self.W[key_i]:
                if key_j not in self.peers:
                    data['nodes'].append({'id': int(index), 'name': key_j})
                    peer_index[key] = index
                    index += 1

        data['links'] = []
        for key_i in self.peers:
            if key_i not in self.W:
                continue
            for key_j in self.W[key_i]:
                if key_j not in self.peers:
                    data['nodes'].append({'name': key_j})
                data['links'].append({
                    'source': int(peer_index[key_i]),
                    'target': int(peer_index[key_j]),
                    'w': self.W[key_i][key_j]
                })

        with open('metagraph.json', 'w') as outfile:
            json.dump(data, outfile)

    def logtostd(self):
        logger.info('N {}', self.peers)
        for key in self.W:
            logger.info('W {} {}', key, list(self.W[key].values()))
        logger.info('R {}', list(self.R.values()))
        logger.info('I {}', list(self.I.values()))
        logger.info('S {}', list(self.S.values()))
   ''' 
