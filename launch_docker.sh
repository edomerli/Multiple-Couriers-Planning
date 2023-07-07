if [[ "$(docker images -q mcp 2> /dev/null)" == "" ]]; then
    docker build -t mcp . 
fi
docker run --mount type=bind,source="$(pwd)/res",target=/src/res -e "instance_file=$1" -e "method=$2" mcp
# TODO: input validation and docs etc./ Readme