rm -r dist/ build/
poetry run python -m grpc_tools.protoc -I protos/ --python_out=. --grpc_python_out=. protos/proto.proto
pyinstaller soundboard.spec
staticx dist/soundboard dist/soundboard.static
