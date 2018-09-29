FROM {band-base-py-image}

LABEL maintainer="Dmitry Rodin <madiedinro@gmail.com>"
LABEL band.service.version="0.3.0"
LABEL band.service.title="Sypex ip2geo"
LABEL band.service.def_position="3x2"

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
    && wget -q -O ./data/sxgdb.zip http://sypexgeo.net/files/SxGeoCityMax_utf8.zip \
    && unzip -o ./data/sxgdb.zip -d ./data

CMD [ "python", "-m", "sxgeo"]
