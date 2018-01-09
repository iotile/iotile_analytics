# Copyright (c) Arch Systems Inc
# Distributed under the terms of the iotile_analytics license

# Pick your favorite docker-stacks image
FROM jupyter/base-notebook

USER jovyan

# Add permanent pip/conda installs, data files, other user libs here
# e.g., RUN pip install jupyter_dashboards

RUN pip install -U pip
RUN pip install qgrid numpy pandas bqplot matplotlib iotile-analytics-core iotile-analytics-interactive
RUN jupyter nbextension enable --py --sys-prefix widgetsnbextension ; jupyter nbextension enable --py --sys-prefix bqplot; jupyter nbextension enable --py --sys-prefix qgrid

EXPOSE 8888
ENTRYPOINT ["jupyter", "notebook"]
