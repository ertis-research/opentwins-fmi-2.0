# pull official base image
FROM python:3.11.3-slim

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
COPY "Single FMU executer/requirements.txt" /usr/src/app/requirements.txt
RUN pip3 install -r requirements.txt

# copy the code shared with the other executers
COPY common /usr/src/app/common

# copy project
COPY "Single FMU executer/." /usr/src/app/

EXPOSE 8001

RUN chmod +x ./run.sh
CMD ["./run.sh"]
