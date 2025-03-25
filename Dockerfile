from ubuntu:20.04

run apt-get update && apt-get install -y binutils git make vim gcc patchelf python-is-python3 python3-pip
run pip3 install requests


workdir /root/how2heap
