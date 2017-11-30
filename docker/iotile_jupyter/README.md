# Jupyter IOTile Analytics Image

This is a Jupyter Docker image with a pre-built iotile_analytics package its dependencies

## To Build

```
docker build -t iotile/iotile_analytics .
```

## To pull from Docker Hub

The latest image is available on https://hub.docker.com/r/iotile/iotile_analytics/, so instead of building, you
can simply pull from the registry:

```
docker pull iotile/iotile_analytics
```

## To run Jupyter Notebook

From another directory, run

```
docker run -it --rm -p 8888:8888 -v $(pwd)/work:/home/jovyan/work iotile/iotile_analytics
```

Note that the above will map a `work` directory where notebooks will be saved.

Once running, it will display the URL with token. e.g.

```
    Copy/paste this URL into your browser when you connect for the first time,
    to login with a token:
        http://localhost:8888/?token=d86f392b7f58467516ad046174e39681edf75f9bbb13c288
```

Copy the localhost URL and paste it in your browser.

To run in the background, replace `--rm` with `-d`, but you will need `docker ps` and `docker logs` 
to find the URL. e.g.

```
$ docker run -it -d -p 8888:8888 -v $(pwd)/work:/home/jovyan/work iotile/iotile_analytics
ae2bd0332ebdd93653d579dfbf215ed2e370d91fd5aae8f7c643c10178056c9f

$ docker ps
CONTAINER ID        IMAGE                    COMMAND                  CREATED                  STATUS              PORTS                                            NAMES
ae2bd0332ebd        iotile_jupyter           "tini -- start-not..."   Less than a second ago   Up 6 seconds        0.0.0.0:8888->8888/tcp                           gallant_lamarr

$ docker logs ae2bd0332ebd
  
    Copy/paste this URL into your browser when you connect for the first time,
    to login with a token:
        http://localhost:8888/?token=d86f392b7f58467516ad046174e39681edf75f9bbb13c288

``` 

## Passing your own Token

To avoid having to get the token from the logs, you can pass your own token:

```
docker run -it --rm -p 8888:8888 -v $(pwd)/work:/home/jovyan/work iotile/iotile_analytics --NotebookApp.token='abc'
```

You can also use `..token=""` to not require a token (not recommended).

## Command-line

You can also use this image to run iPython or any regular python scripts (taking advantage of all installed packages):

```
# iPython:
docker run -it --rm --entrypoint ipython iotile/iotile_analytics

# Running Python script
docker run -it --rm --entrypoint python -v $(pwd):/home/jovyan iotile/iotile_analytics foo.py
```

## Docker Compose

A convenient way to store the configuration (to avoid so much typing on the cmd line) is to use docker-compose. 
The following snippet shows a possible `docker-compose.yml` file

```
version: '2'
services:

  iotile:
    image: iotile/iotile_analytics
    volumes:
      - ./work:/home/jovyan/work
    ports:
      - "8888:8888"
    command: --NotebookApp.token='abc'
```

and then, simply run

```
docker-compose up -d   # To run image in background
docker-compose run --rm --entrypoint python iotile foo.py # to run work/foo.py script
```



