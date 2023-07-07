FROM minizinc/minizinc:latest

WORKDIR /src

COPY . .

RUN apt-get update \
 && apt-get install -y python3 \
 && apt-get install -y python3-pip \
 && python3 -m pip install -r requirements.txt 

ENV instance_file=""
ENV method=""

CMD python3 run_master.py $instance_file $method

