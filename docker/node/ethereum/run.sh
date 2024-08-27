#! /bin/bash

mkdir -p /data/geth/chaindata
mkdir -p /data/geth/logs
mkdir -p /data/lighthouse/chaindata
mkdir -p /data/lighthouse/logs

nohup geth --datadir "/data/geth/chaindata" \
--http.corsdomain "*" \
--http \
--http.addr 0.0.0.0 \
--http.port 8545 \
--http.corsdomain "*" \
--http.api admin,debug,web3,eth,txpool,net \
--http.vhosts "*" \
--ws \
--ws.addr 0.0.0.0 \
--ws.port 8546 \
--ws.origins "*" \
--ws.api admin,debug,web3,eth,txpool,net \
--gcmode full \
--cache 8192 \
--mainnet \
--metrics \
--metrics.addr 127.0.0.1 \
--syncmode snap \
--authrpc.vhosts="localhost" \
--authrpc.port 8551 \
--authrpc.jwtsecret=~/.secret/jwtsecret \
--txpool.accountslots 16 \
--txpool.globalslots 1024 \
--txpool.accountqueue 64 \
--txpool.globalqueue 512 \
--nat extip:$(hostname -i) \
&> "/data/geth/logs/geth.log" &

nohup lighthouse bn \
--network mainnet \
--http \
--metrics \
--datadir /data/lighthouse/chaindata \
--execution-jwt ~/.secret/jwtsecret \
--execution-endpoint http://localhost:8551 \
--checkpoint-sync-url https://sync-mainnet.beaconcha.in \
--disable-deposit-contract-sync \
&> "/data/lighthouse/logs/lighthouse.log" &
