# Build protos.
	python3 -m grpc.tools.protoc metagraph_proxy/metagraph.proto  -I. --python_out=. --grpc_python_out=.
