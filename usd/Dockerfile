FROM alpine:3 AS Builder
WORKDIR /src

RUN apk update \
  && apk upgrade \
  && apk add --no-cache \
    clang \
    clang-dev \
    alpine-sdk \
    cmake \
    ccache \
    git \
    'python3<3.12' \
    'python3-dev<3.12'

RUN apk add --no-cache \
    py3-jinja2

# Build a patched, legacy version of TBB for USD
RUN apk add --no-cache \
    curl \
    linux-headers

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

#RUN git clone --depth 1 https://github.com/PixarAnimationStudios/USD



#RUN cd USD && g++ --version && python3 build_scripts/build_usd.py \
#    -vvv \
#    --dry_run \
#    --build-variant=release \
#    --src=/src/deps \
#    --inst=/opt/USD-deps \
#    --no-tests \
#    --no-examples \
#    --no-tutorials \
#    --no-imaging \
#    /opt/USD

#RUN apk add --no-cache \
#    boost-dev

#    -DBOOST_ROOT=/usr/lib \
#RUN cmake \
#    -DTBB_ROOT_DIR=/opt/vendored \
#    -DPXR_BUILD_USD_IMAGING=FALSE \
#    -DPXR_BUILD_IMAGING=OFF \
#    -DPXR_ENABLE_GL_SUPPORT=FALSE \
#    -DPXR_ENABLE_MATERIALX_SUPPORT=FALSE \
#    -DPXR_BUILD_EXAMPLES=FALSE \
#    -DPXR_BUILD_DOCUMENTATION=FALSE \
#    -DPXR_BUILD_TUTORIALS=FALSE \
#    ./USD

#RUN cd USD && cmake --build . --target install

ENTRYPOINT [ "/opt/USD/bin/usdcat", "-h" ]

