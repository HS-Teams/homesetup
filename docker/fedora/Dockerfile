FROM fedora

LABEL maintainer="Hugo Saporetti Junior<taius.hhs@gmail.com>"

USER root

ENV SHELL='/bin/bash'
ENV HOME='/root'

RUN yum -y update
RUN yum install -y sudo redhat-rpm-config curl vim git findutils procps procps-ng hostname uptimed glibc-common
RUN yum install -y gcc postgresql-devel rsync file cmake ruby ruby-devel xclip net-tools
RUN yum install -y bat fd-find fzf gawk
RUN yum install -y python3.11 python3.11-devel portaudio-devel ffmpeg
RUN yum clean all
RUN gem install colorls
RUN curl -O https://bootstrap.pypa.io/get-pip.py
RUN $(which python3.11) get-pip.py

WORKDIR "${HOME}"

RUN curl -o- https://raw.githubusercontent.com/yorevs/homesetup/master/install.bash | bash

CMD ["bash", "--login"]
