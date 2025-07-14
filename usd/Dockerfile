FROM alpine:3 AS builder
WORKDIR /src

RUN apk update \
  && apk upgrade \
  && apk add --no-cache \
    alpine-sdk \
    boost-dev \
    ccache \
    clang \
    clang-dev \
    cmake \
    curl \
    git \
    linux-headers \
    onetbb \
    onetbb-dev \
    'python3<3.13' \
    'python3-dev<3.13' \
    py3-jinja2

# Build USD

RUN git clone --single-branch  -b v25.05.01-alpine --depth 1 https://github.com/rstelzleni/USD

RUN mkdir /src/USD-build
WORKDIR /src/USD-build

RUN cmake \
    -DPXR_BUILD_USD_IMAGING=FALSE \
    -DPXR_BUILD_IMAGING=FALSE \
    -DPXR_ENABLE_GL_SUPPORT=FALSE \
    -DPXR_ENABLE_MATERIALX_SUPPORT=FALSE \
    -DPXR_BUILD_TESTS=FALSE \
    -DPXR_BUILD_EXAMPLES=FALSE \
    -DPXR_BUILD_DOCUMENTATION=FALSE \
    -DPXR_BUILD_TUTORIALS=FALSE \
    -DCMAKE_INSTALL_PREFIX=/opt/USD \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_CXX_FLAGS="-Os -s" \
    /src/USD

RUN cmake --build . --config Release --target install -j8

# Before shipping a new version uncomment below to run tests. Tests also need
# to be enabled in the cmake command above
#
# Since builds are repeatable once they're passing we can disable to save time
# on docker builds.
#
# RUN ctest

# Make the trimmed down image

FROM alpine:3
COPY --from=builder /opt /opt
ENV PYTHONPATH=/opt/USD/lib/python

RUN apk update \
  && apk upgrade \
  && apk add --no-cache \
    boost-python3 \
    onetbb \
    'python3<3.13'

ENTRYPOINT [ "/opt/USD/bin/usdcat" ]

