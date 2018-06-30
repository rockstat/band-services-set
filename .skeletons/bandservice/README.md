


## Hot to start

### 1. Take name for your service

for example `pikachu`

### 2. Copy skeleton template. Folder should have name same with service

    cp -R band-py pikachu

### 3. Configure service name

1. Rename `skeleton` subfolder to service name
2. Set `name:` to your service name in config.yaml
3. Set name in Dockerfile at the end `CMD [ "python", "-m", "pikachu"]`

