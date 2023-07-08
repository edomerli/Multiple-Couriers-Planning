#!/usr/bin/env bash
if ! docker info > /dev/null 2>&1; then
  echo "This script uses docker, and it isn't running - please start docker and try again!"
  sleep 3
  exit 1
fi

if [[ "$(docker images -q mcp 2> /dev/null)" == "" ]]; then
    docker build -t mcp . 
    sleep 10
fi
docker run --mount type=bind,source="$(pwd)/res",target=/src/res -e "instance_file=$1" -e "method=$2" mcp
sleep 10
# TODO: input validation and docs etc./ Readme