# CDMO Project
 Project of the course Combinatorial Decision Making and Optimization from the Master degree in Artificial Intelligence, University of Bologna 2022/2023

## Usage
To run the models of one of the four methods on a given instance using docker, use the command:
```console
$ launch_docker.sh <instance_file> <method>
```
where:
* `<instance_file>` is the path of the **relative** path of the instance to run w.r.t. the project root directory (this directory)
* `<method>` is one among {CP, SAT, SMT, MIP}