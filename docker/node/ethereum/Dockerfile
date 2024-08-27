FROM ubuntu:22.04

RUN apt update -y
RUN apt-get update -y
RUN apt install -y dstat jq curl wget software-properties-common
RUN curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
RUN bash add-google-cloud-ops-agent-repo.sh --also-install
RUN rm add-google-cloud-ops-agent-repo.sh

RUN add-apt-repository -y ppa:ethereum/ethereum
RUN apt-get -y install ethereum
RUN geth version
RUN wget https://github.com/sigp/lighthouse/releases/download/v5.1.1/lighthouse-v5.1.1-x86_64-unknown-linux-gnu.tar.gz
RUN tar -xvf ./lighthouse-v5.1.1-x86_64-unknown-linux-gnu.tar.gz
RUN rm ./lighthouse-v5.1.1-x86_64-unknown-linux-gnu.tar.gz
RUN mv lighthouse /usr/bin
RUN lighthouse --version

RUN mkdir ~/.secret
RUN openssl rand -hex 32 > ~/.secret/jwtsecret
RUN chmod 440 ~/.secret/jwtsecret

COPY ./run.sh ./run.sh
RUN chmod +x ./run.sh
CMD ./run.sh & sleep infinity
