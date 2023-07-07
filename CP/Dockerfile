FROM minizinc/minizinc:latest

WORKDIR /src

COPY . .

RUN apt-get update \
 && apt-get install -y python3 \
 && apt-get install -y python3-pip \
 && python3 -m pip install -r requirements.txt 

ARG instance_file

CMD python3 run.py $instance_file