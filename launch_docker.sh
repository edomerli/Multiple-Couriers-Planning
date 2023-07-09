#!/usr/bin/env bash
if [ $# -lt 2 ]; then
    echo "2 arguments expected, $# were given"
    echo "Usage: `basename "$0"` instance_file_path method"
    read -n 1 -s -r -p "Press any key to continue"
    exit 1
fi

if [ ! docker info > /dev/null 2>&1 ]; then
  echo "This script uses docker, and it isn't running - please start docker and try again!"
  read -n 1 -s -r -p "Press any key to continue"
  exit 1
fi

if [[ "$(docker images -q mcp 2> /dev/null)" == "" ]]; then
    docker build -t mcp . 
fi
echo "Starting run of instance $1 using method $2"
docker run --mount type=bind,source="$(pwd)/res",target=/src/res -e "instance_file=$1" -e "method=$2" --log-driver none mcp
read -n 1 -s -r -p "Press any key to continue"

