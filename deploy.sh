#!/bin/bash

if [ -z "$PLATFORM" ]; then
  PLATFORM="linux/arm64"
fi

docker buildx build  --tag sipmcalib_control --platform ${PLATFORM} --rm --load ./
docker run -it -p 9100:9100 --platform ${PLATFORM} sipmcalib_control:latest ${@}
