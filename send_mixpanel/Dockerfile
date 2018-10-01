FROM {band-base-py-image}

LABEL maintainer="Dmitry Rodin <madiedinro@gmail.com>"
LABEL band.service.version="0.3.0"
LABEL band.service.title="Mixpanel uploader"
LABEL band.service.def_position="3x1"

WORKDIR /usr/src/services

ENV HOST=0.0.0.0
ENV PORT=8080

#cachebust
ARG RELEASE=master
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE ${PORT}
COPY . .

CMD [ "python", "-m", "send_mixpanel"]
