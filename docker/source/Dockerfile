FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update -y
RUN apt install software-properties-common -y
RUN add-apt-repository ppa:deadsnakes/ppa -y
RUN apt install python3 python3-pip -y

COPY requirements requirements

RUN apt update
RUN apt install rustc cargo -y
RUN pip3 install -r requirements/runtime.txt

COPY pyrevm pyrevm
WORKDIR pyrevm
RUN VIRTUAL_ENV=$(python3 -c 'import sys; print(sys.base_prefix)') pip3 install .
WORKDIR /
COPY src src
COPY main.py main.py
COPY docker/source/run.sh run.sh
RUN chmod +x run.sh
CMD ./run.sh & sleep infinity
