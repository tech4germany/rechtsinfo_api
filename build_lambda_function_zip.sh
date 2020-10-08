#!/bin/bash -x

# Cf. https://docs.aws.amazon.com/lambda/latest/dg/python-package.html#deployment-pkg-for-virtualenv
python -m venv deploy_venv
deploy_venv/bin/python -m pip install --no-deps .
cd deploy_venv/lib/python*/site-packages
zip -9yqr ${OLDPWD}/lambda_function.zip rechtsinfo* rip_api
cd ${OLDPWD}
rm -r deploy_venv
