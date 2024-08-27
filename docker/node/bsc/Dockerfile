FROM ubuntu:22.04

RUN apt update -y
RUN apt-get update -y
RUN apt install -y dstat jq curl wget software-properties-common
RUN curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
RUN bash add-google-cloud-ops-agent-repo.sh --also-install
RUN rm add-google-cloud-ops-agent-repo.sh

RUN apt install unzip -y

# https://docs.bnbchain.org/docs/BSC-fast-node/#download-the-pre-build-binaries-from-release-page-or-follow-the-instructions-below
RUN wget $(curl -s https://api.github.com/repos/bnb-chain/bsc/releases/latest |grep browser_ |grep geth_linux |cut -d\" -f4)
RUN mv geth_linux geth
RUN chmod -v u+x geth

RUN wget $(curl -s https://api.github.com/repos/bnb-chain/bsc/releases/latest |grep browser_ |grep mainnet |cut -d\" -f4)
RUN unzip mainnet.zip

# Install golang
RUN wget https://go.dev/dl/go1.22.2.linux-amd64.tar.gz
RUN tar -C /usr/local -xzf go1.22.2.linux-amd64.tar.gz
ENV PATH=$PATH:/usr/local/go/bin
RUN rm go1.22.2.linux-amd64.tar.gz

RUN apt install -y build-essential git
RUN git clone -b v2.128.95 https://github.com/bloXroute-Labs/gateway
RUN mv /gateway /gateway_repo
WORKDIR /gateway_repo
RUN make
RUN mv /gateway_repo/bin/gateway /gateway
RUN mv /gateway_repo/bin/bxcli /bxcli
WORKDIR /
RUN chmod +x /gateway
RUN chmod +x /bxcli
RUN rm -rf /gateway_repo

RUN apt install -y python3-pip
RUN pip install flask web3

COPY ./config.toml ./config.toml

COPY ./nodekey ./nodekey
COPY ./bloxroute ./ssl
RUN mkdir -p /ssl/external_gateway/ca
RUN curl https://s3.amazonaws.com/credentials.blxrbdn.com/ca/ca_cert.pem -o /ssl/external_gateway/ca/ca_cert.pem

COPY ./sync_checker.sh ./sync_checker.sh
RUN chmod +x ./sync_checker.sh

COPY ./load_balancer_health_checker.py ./load_balancer_health_checker.py

COPY ./run.sh ./run.sh
RUN chmod +x ./run.sh
CMD ./run.sh & sleep infinity
