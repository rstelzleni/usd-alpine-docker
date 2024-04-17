FROM alpine:3 AS Builder
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
    'python3<3.12' \
    'python3-dev<3.12' \
    py3-jinja2

# Build a patched, legacy version of TBB for USD

RUN curl https://github.com/oneapi-src/oneTBB/archive/refs/tags/v2020.3.zip -o ./TBBv2020.3.zip -L
COPY patches .
RUN unzip ./TBBv2020.3.zip && cd oneTBB-2020.3 && \
    patch include/tbb/task.h ../missing-namespace.patch && \
    patch src/tbbmalloc/proxy.h ../disable-malloc-hook.patch && \
    patch src/tbbmalloc/proxy.cpp ../prevent-undefined-glibc-macro-error.patch && \
    make && \
    mkdir /opt/vendored && \
    mkdir /opt/vendored/lib && \
    mkdir /opt/vendored/include && \
    cp build/*_release/libtbb*.* /opt/vendored/lib && \
    cp -R include/serial /opt/vendored/include/ && \
    cp -R include/tbb /opt/vendored/include/

# Build USD

RUN git clone --single-branch  -b v24.03-alpine --depth 1 https://github.com/rstelzleni/USD

RUN mkdir /src/USD-build
WORKDIR /src/USD-build

RUN cmake \
    -DTBB_ROOT_DIR=/opt/vendored \
    -DCMAKE_PREFIX_PATH=/opt/vendored \
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

# Make the final image

FROM alpine:3
COPY --from=Builder /opt /opt
ENV PYTHONPATH=/opt/USD/lib/python

RUN apk update \
  && apk upgrade \
  && apk add --no-cache \
    boost-python3 \
    'python3<3.12'

ENTRYPOINT [ "/opt/USD/bin/usdcat", "-h" ]

