#!/bin/bash -x

./build_lambda_deps_layer.sh
cd lambda_deps
zip -9yqr ../lambda_deps.zip python
cd ..
rm -r lambda_deps
