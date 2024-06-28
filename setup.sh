#! /bin/bash
# このファイルが有る場所をカレントディレクトリとする
cd `dirname ${0}`
pwd

python3 -m venv .venv

. .venv/bin/activate

pip install -r requirements.txt

deactivate