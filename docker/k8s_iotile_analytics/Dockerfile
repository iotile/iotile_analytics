# Copyright (c) Arch Systems Inc
# Distributed under the terms of the iotile_analytics license

FROM iotile/iotile_analytics

USER $NB_USER

ARG JUPYTERHUB_VERSION=0.8
RUN pip install --no-cache jupyterhub==$JUPYTERHUB_VERSION

ENTRYPOINT ["tini", "--"]

