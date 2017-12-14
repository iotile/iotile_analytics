# Jupyter IOTile Analytics Image

This is a Jupyter Docker image with a pre-built iotile_analytics package and its dependencies. It is tailored for Kubernetes, in combination with JupyterHub.

## To Build

```
docker build -t iotile/k8s_iotile_analytics .
```

## To pull from Docker Hub

The latest image is available on https://hub.docker.com/r/iotile/k8s_iotile_analytics/, so instead of building, you
can simply pull from the registry:

```
docker pull iotile/k8s_iotile_analytics
```
