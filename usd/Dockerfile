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


RUN git clone --depth 1 https://github.com/PixarAnimationStudios/USD


RUN apk add --no-cache \
    linux-headers

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

RUN apk add --no-cache \
    boost-dev \
    onetbb

RUN apk add --no-cache onetbb-dev

#    -DBOOST_ROOT=/usr/lib \
#    -DTBB_ROOT_DIR=/usr/lib \
RUN cmake \
    -DPXR_BUILD_USD_IMAGING=FALSE \
    -DPXR_BUILD_IMAGING=OFF \
    -DPXR_ENABLE_GL_SUPPORT=FALSE \
    -DPXR_ENABLE_MATERIALX_SUPPORT=FALSE \
    -DPXR_BUILD_EXAMPLES=FALSE \
    -DPXR_BUILD_DOCUMENTATION=FALSE \
    -DPXR_BUILD_TUTORIALS=FALSE \
    ./USD

#RUN cd USD && cmake --build . --target install

ENTRYPOINT [ "/opt/USD/bin/usdcat", "-h" ]

