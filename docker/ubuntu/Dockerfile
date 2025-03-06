FROM ubuntu

LABEL maintainer="Hugo Saporetti Junior<taius.hhs@gmail.com>"

USER root

ENV SHELL='/bin/bash'
ENV HOME='/root'

RUN apt-get update
RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa -y
RUN apt-get update
RUN apt-get install -y sudo build-essential curl procps file vim git rsync file cmake ruby ruby-dev bsdmainutils
RUN apt-get install -y bat fd-find fzf gawk locales libpq-dev libnl-3-dev
RUN apt-get install -y python3.11 python3.11-dev portaudio19-dev  ffmpeg
RUN gem install colorls
RUN locale-gen "en_US.UTF-8"
RUN curl -O https://bootstrap.pypa.io/get-pip.py
RUN $(which python3.11) get-pip.py
RUN $(which python3.11) -m pip install --ignore-installed setuptools wheel

WORKDIR "${HOME}"

RUN curl -o- https://raw.githubusercontent.com/yorevs/homesetup/master/install.bash | bash

CMD ["bash", "--login"]
