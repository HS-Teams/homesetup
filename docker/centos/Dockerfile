FROM centos

LABEL maintainer="Hugo Saporetti Junior<taius.hhs@gmail.com>"

USER root

ENV SHELL='/bin/bash'
ENV HOME='/root'

RUN sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-*
RUN sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*
RUN yum update -y
RUN yum install -y sudo curl vim wget procps-ng glibc-common libpq-devel file cmake git openssl-devel bzip2-devel
RUN yum install -y libffi-devel rsync sqlite-devel alsa-lib-devel
RUN yum groupinstall -y "Development Tools"
RUN wget https://www.python.org/ftp/python/3.11.11/Python-3.11.11.tgz
RUN tar -xzf Python-3.11.11.tgz

WORKDIR "Python-3.11.11"

RUN ./configure --enable-optimizations --enable-loadable-sqlite-extensions
RUN make install

RUN wget https://files.portaudio.com/archives/pa_stable_v190700_20210406.tgz
RUN tar -xzf pa_stable_v190700_20210406.tgz

WORKDIR "portaudio"

RUN ./configure
RUN make install

WORKDIR "${HOME}"

RUN curl -o- https://raw.githubusercontent.com/yorevs/homesetup/master/install.bash | bash

CMD ["bash", "--login"]
