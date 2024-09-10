# pull official base image
FROM python:3.11.3-slim

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
COPY requirements.txt /usr/src/app
RUN pip3 install -r requirements.txt

# copy project
COPY . /usr/src/app/

EXPOSE 8001

RUN chmod +x ./run.sh
CMD ["./run.sh"]
