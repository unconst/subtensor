from substrateinterface import SubstrateInterface, Keypair, SubstrateRequestException
from substrateinterface.utils.ss58 import ss58_encode

substrate = SubstrateInterface(
    url="ws://localhost:9944/",
    address_type=2,
    type_registry_preset='kusama'
)

# Block_hash set to None for chaintip.
block_hash = None

neuron_vec = substrate.get_runtime_state(
        module='BittensorModule',
        storage_function='Neurons',
        params=[],
        block_hash=block_hash
    ).get('result')
print("Neurons: {}".format(neuron_vec))

# Create keypair.
mnemonic = Keypair.generate_mnemonic()
keypair = Keypair.create_from_mnemonic(mnemonic, 2)
print("Created address: {}".format(keypair.ss58_address))


# Submit subscribe transaction.
call = substrate.compose_call(
    call_module='BittensorModule',
    call_function='subscribe',
    call_params={
    }
)
extrinsic = substrate.create_signed_extrinsic(call=call, keypair=keypair)
try:
    # result = substrate.send_extrinsic(extrinsic)
    result = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)

    print('Extrinsic "{}" included in block "{}"'.format(
        result['extrinsic_hash'], result.get('block_hash')
    ))

except SubstrateRequestException as e:
    print("Failed to send: {}".format(e))
