# 
# Copyright (C) 2025 Matteo Repetto <mattereppe@gmail.com>
#
# This file is part of the otupy framework.
# 
# Docker image with otupy software.
# Base Docker image from: https://hub.docker.com/_/python/
# 
# Check the container image for copyright and licenses that apply to the
# included software (/usr/share/doc/*/copyright).
#
# v1.0.0
#
# Build options:
# VERSION: release tag to use

FROM python:3-trixie

# Optionally take an argument to specify the otupy version to use
ARG VERSION=""

# Install and activate a virtual environment
RUN python -m venv /opt/otupy-venv
ENV PATH="/opt/otupy-venv/bin:$PATH"

ENV TZ="Europe/Rome"


RUN if [ -n "$VERSION" ]; then \
		OTUPY_VERSION="==$VERSION"; \
	 fi; \
	echo "Otupy version:  ${OTUPY_VERSION}"; \
	pip install otupy$OTUPY_VERSION;

RUN mkdir -p /config/configs

WORKDIR /apps/

RUN cp -a /opt/otupy-venv/lib/python3*/site-packages/otupy/apps/*  .
COPY connector.yaml /config/
COPY discovery.yaml /config/

CMD ["python3", "connector/connector.py", "-c", "/config/connector.yaml"] 

