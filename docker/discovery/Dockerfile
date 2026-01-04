# 
# Copyright (C) 2025 Matteo Repetto <mattereppe@gmail.com>
#
# This file is part of the otupy framework.
# 
# Docker image with otupy software.
# Base Docker image from: ghcr.io/mattereppe/discovery
# 
# Check the container image for copyright and licenses that apply to the
# included software (/usr/share/doc/*/copyright).
#
# v1.0.0
#
# Build options:
# VERSION: release tag to use

# Optionally take an argument to specify the otupy version to use
ARG VERSION="latest"

FROM ghcr.io/mattereppe/otupy:$VERSION

RUN cp -a /opt/otupy-venv/lib/python3*/site-packages/otupy/apps/ctxd/discovery.py  .

CMD ["python3", "discovery.py", "-c", "/config/discovery.yaml", "--host", "0.0.0.0", "-p", "80", "--api"]
