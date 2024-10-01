#!/usr/bin/env bash
docker build -t registry.ertis.uma.es/opentwins-fmu-runner-single-v2 Single\ FMU\ executer/.
docker build -t registry.ertis.uma.es/opentwins-fmu-runner-multiple-v2 Multiple\ FMU\ executer/.

docker push registry.ertis.uma.es/opentwins-fmu-runner-single-v2
docker push registry.ertis.uma.es/opentwins-fmu-runner-multiple-v2