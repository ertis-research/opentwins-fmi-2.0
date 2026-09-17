#!/usr/bin/env bash
# Build context is the repo root so both images can also COPY the shared "common/" package.
docker build -t docker.ertis.uma.es/fmi-release/opentwins-fmu-runner-single-v2 -f "Single FMU executer/Dockerfile" .
docker build -t docker.ertis.uma.es/fmi-release/opentwins-fmu-runner-multiple-v2 -f "Multiple FMU executer/Dockerfile" .

docker push docker.ertis.uma.es/fmi-release/opentwins-fmu-runner-single-v2
docker push docker.ertis.uma.es/fmi-release/opentwins-fmu-runner-multiple-v2
