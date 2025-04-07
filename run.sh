#!/bin/zsh

python -m weibo_spider --config_path="config.json" > run.log 2 >& 1 &
