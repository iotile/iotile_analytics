# Copyright (c) Arch Systems Inc
# Distributed under the terms of the iotile_analytics license

# Pick your favorite docker-stacks image
FROM jupyter/datascience-notebook

USER jovyan

# Add permanent pip/conda installs, data files, other user libs here
# e.g., RUN pip install jupyter_dashboards

RUN pip install -U pip
RUN pip install iotile_analytics

USER root

# Add permanent apt-get installs and other root commands here
# e.g., RUN apt-get install npm nodejs