# Jupyter IOTile Analytics Image

This is a Jupyter Docker image with a pre-built iotile_analytics package its dependencies

## To Build

```
docker build -t iotile_jupyter .
```

## To run

From another directory, run

```
docker run -it --rm -p 8888:8888 -v $(pwd)/work:/home/jovyan/work  iotile_jupyter
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
$ docker run -it -d -p 8888:8888 -v $(pwd)/work:/home/jovyan/work  iotile_jupyter
ae2bd0332ebdd93653d579dfbf215ed2e370d91fd5aae8f7c643c10178056c9f

$ docker ps
CONTAINER ID        IMAGE                    COMMAND                  CREATED                  STATUS              PORTS                                            NAMES
ae2bd0332ebd        iotile_jupyter           "tini -- start-not..."   Less than a second ago   Up 6 seconds        0.0.0.0:8888->8888/tcp                           gallant_lamarr

$ docker logs ae2bd0332ebd
  
    Copy/paste this URL into your browser when you connect for the first time,
    to login with a token:
        http://localhost:8888/?token=d86f392b7f58467516ad046174e39681edf75f9bbb13c288

``` 

