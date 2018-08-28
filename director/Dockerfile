FROM rockstat/band-base-py
LABEL maintainer="Dmitry Rodin <madiedinro@gmail.com>"

WORKDIR /usr/src/services

ENV HOST=0.0.0.0
ENV PORT=8080
RUN apt-get update && apt-get install -y --no-install-recommends \
	&& rm -rf /var/lib/apt/lists/*

#cachebust
ARG RELEASE=master

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE ${PORT}
COPY . .

CMD [ "python", "-m", "director"]
