FROM {band-base-py-image}

LABEL maintainer="Dmitry Rodin <madiedinro@gmail.com>"
LABEL band.service.version="0.2.1"
LABEL band.service.title="MaxMind ip2geo"
LABEL band.service.def_position="2x2"

WORKDIR /usr/src/services

ENV HOST=0.0.0.0
ENV PORT=8080

#cachebust
ARG RELEASE=master
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE ${PORT}
COPY . .

RUN mkdir -p data \
    && wget -q -O ./data/a.zip http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.tar.gz \
    && tar -zxf ./data/a.zip --strip=1 -C ./data


CMD [ "python", "-m", "mmgeo"]
