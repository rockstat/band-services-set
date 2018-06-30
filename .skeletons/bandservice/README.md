# Band service skeleton



## Hot to start

### 1. Service name

First give a name to new service (in your mind). For example `pikachu`

### 2. Copy skeleton

User images of services should be located in `my_images` directory. To distplay current location execute `pwd`
Open terminal (file -> new terminal), and make a copy of skeleton sources. Assuming you terminal session located at ~/projects. Run command:

```bash
cp -R sources/skeletons_ro/bandservice my_images/pikachu
```

### 3. Define service name

1. using IDE rename subfolder `bandservice` to your new service name
2. Set `name:` property to your service name in `config.yaml`
3. Set name in Dockerfile at the end `CMD [ "python", "-m", "SERVICE_NAME"]`

So you result looks should be looks like that:

```
my_images
| - pikachu
    | - .dockerignore
    | - config.yaml
    | - Dockerfile
    | - requirements.txt
    | - start_dev
    | - pikachu
        | - __init__.py
        | - __main__.py
        | - main.py
```

### Short introduction to Band services.

All of code splitting into logocal services. Service could contains number of functions, that can exposed to other services or event outside (to works) using `frontier (front service)` proxing mechanics. Each function can take one of difined roles:

- **listener**: listener for all events matching provided key. That role uses database writers and streaming services
- **enricher**: provides additional data chunks (enrichments) for events matched provided rules. Returened data will be attached to incoming event
- **handler**: fucnctin result will be returned back to event initiator

Moreover you can define function as woker which load initial data or packet hanldle incoming data

- **task**: worker function

### Coding your service

Look into `yourservice/yourservice/main.py` it template of a new services, which can be `handler` or `enricher`

### Running for debug

Ensure you located at your service root directory and directory contains `start_dev`. 
> For newbies: list files using `ls`, current directory `pwd` 

execute 
```
./run_dev
```


