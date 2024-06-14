# USD Alpine Docker

USD builds in alpine docker, for making slim docker containers with USD support.

Builds available on dockerhub
https://hub.docker.com/repository/docker/rstelzleni/usd-alpine/general

## Versions

### usd-24.05

base: ~45 MB download
imaging: ~57 MB download
gl: ~142 MB download

Base has the same contents as 24.03. Imaging and GL are new images that add
usdImaging support and add a virtual framebuffer for software GL rendering.

There are some new test failures with shaders in testUsdChecker. I didn't get
to the bottom of these. My guess is this is not specific to the Alpine version.

### usd-24.03

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

Imaging containers are published like

```
docker buildx build --platform linux/arm64,linux/amd64 --tag rstelzleni/usd-alpine:imaging-24.05 --tag rstelzleni/usd-alpine:imaging-latest --builder=multi-builder -f Dockerfile.imaging-base --push .
docker buildx build --platform linux/arm64,linux/amd64 --tag rstelzleni/usd-alpine:gl-24.05 --tag rstelzleni/usd-alpine:gl-latest --builder=multi-builder -f Dockerfile.gl --push .
```

When publishing tag this github repo and the USD branch to match the usd-alpine
tag. For instance, if the dockerhub repo is rstelzleni/usd-alpine:usd-24.05

```
git tag -a usd-24.05 -m "code used for dockerhub rstelzleni/usd-alpine:usd-24.05"
git push origin tag usd-24.05
```

### Syncing USD from upstream

Example for version 24.05, with change ids from v24.03-alpine

```
git fetch --tags upstream
git checkout v24.05
git switch -c v24.05-alpine
git cherry-pick \
    50fd0de8c013bff74449c50773a1fadbb462ae54 \
    a4eb20b6d406a6e9aab623b91643a3b661d1b97c \
    71d554e9a069dd8b4c8a3caa2de62a0cf7f00482 \
    94ffb191848e1d8d983b5eecee7128419fe89f48 \
    1a7035a544c1d98fa70dfd22ee9277c999b3736b \
    d88df78612519dd998aeee5dbe08267c91b3394f \
    4b4279385bcd33533437948a88210540566bf385 \
    509b15fe0f8f3fb5fdd37153eff5c5f838965e16 \
    d4c7d1c89cfa6841214cd64776026a63ccf10f69 \
    43730d234749f7349c494ec4e327c5ff58e17ede
```

