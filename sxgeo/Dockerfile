FROM rockstat/band-base-py
LABEL maintainer="Dmitry Rodin <madiedinro@gmail.com>"

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
