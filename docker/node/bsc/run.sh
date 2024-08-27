#! /bin/bash

mkdir -p /data/gateway
mkdir -p /data/geth/logs

nohup sudo ./geth --tries-verify-mode none --config config.toml --datadir "/data" \
--rpc.allow-unprotected-txs --history.transactions 0 \
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
--syncmode snap \
--nat extip:$(hostname -i) \
--db.engine=pebble \
| sudo tee -a /data/geth/log.log &

sleep 10

mkdir -p /datadir
nohup ./gateway --blockchain-network BSC-Mainnet \
--port 1801 \
--enodes enode://ee72a735e9ce002f94c3909d8ce159146697c354fc2bad6c566feaf22de4e6f9757713043edae67bf3d26e78bd30141f4524b6562addc2d9f390fc0828f51224@127.0.0.1:30303 \
--private-key 6347f7dedadf24ebc6d00fa1b60ff73c0ea4167bbd79809cc5a2db238a1d9110 \
--eth-ws-uri ws://0.0.0.0:8546 \
--relay-ip 54.157.119.190 \
--mode bdn,flashbots \
--all-txs true \
--enable-blockchain-rpc true \
--tx-include-sender-in-feed false &> "/data/gateway/gateway.log" &

nohup python3 load_balancer_health_checker.py &
