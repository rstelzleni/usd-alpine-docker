# USD Alpine Docker

USD builds in alpine docker, for making slim docker containers with USD support.

The v24.03 builds are around a 45 MB download.

## Versions

### v24.03

~45 MB download

Includes only the core libraries, no Alembic, MaterialX, etc. Includes Python
3.11 with USD python libraries.

## Dev Process

To make a new version, work in a USD branch that is cloned in the Dockerfile,
for instance,

https://github.com/rstelzleni/USD/tree/v24.03-alpine

Build and run tests in the docker container. Once tests are passing, tests
can be commented back out to shorten build times.

When ready to publish, I've been publishing like

```
cd usd
docker buildx build --platform linux/arm64,linux/amd64 --tag rstelzleni/usd-alpine:usd-24.03  --tag rstelzleni/usd-alpine:latest --builder=multi-builder --push .
```

When publishing tag this github repo and the USD branch to match the usd-alpine
tag. For instance, if the dockerhub repo is rstelzleni/usd-alpine:usd-24.03

```
git tag -a usd-24.03 -m "my tag comment"
git push origin usd-24.03
```

