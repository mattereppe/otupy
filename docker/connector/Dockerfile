# 
# Copyright (C) 2025 Matteo Repetto <mattereppe@gmail.com>
#
# This file is part of the otupy framework.
# 
# Docker image with otupy software.
# Base Docker image from: ghcr.io/mattereppe/otupy
# 
# Check the container image for copyright and licenses that apply to the
# included software (/usr/share/doc/*/copyright).
#
# v1.1.0 
# 
# HISTORY
# v1.0.0 - Plain MIRANDA connector with otupy actuators
# v1.1.0 - MIRANDA connector including security agents (Filebeat, Packetbeat, Metricbeat, fprobe)
#
# Build options:
# OTUPY_VERSION: release tag to use
# ELASTIC_VERSION: Elastic version to use


# Optionally take an argument to specify the otupy version to use
ARG OTUPY_VERSION="latest"
ARG ELASTIC_VERSION="9.x"

FROM ghcr.io/mattereppe/otupy:$OTUPY_VERSION

# Install otupy connector package
RUN cp -a /opt/otupy-venv/lib/python3*/site-packages/otupy/apps/connector/connector.py  .
RUN mkdir /actuators-config

# Install security agents
ARG ELASTIC_VERSION
ENV DEBIAN_FRONTEND=noninteractive
RUN wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch  | gpg --dearmor -o /etc/apt/keyrings/elastic-archive-keyring.pgp  && \
		 echo "deb [signed-by=/etc/apt/keyrings/elastic-archive-keyring.pgp] https://artifacts.elastic.co/packages/${ELASTIC_VERSION}/apt stable main"  | \ 
		 	tee -a /etc/apt/sources.list.d/elastic-${ELASTIC_VERSION}.list && \
		 apt-get update  && \ 
		 apt-get install -y filebeat packetbeat metricbeat fprobe iptables


CMD ["python3", "connector.py", "-c", "/config/connector.yaml"]
