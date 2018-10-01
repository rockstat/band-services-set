FROM {band-base-py-image}
WORKDIR /usr/src/services

LABEL maintainer="Dmitry Rodin <madiedinro@gmail.com>"
LABEL band.service.version="0.3.0"
LABEL band.service.title="Debug service"
LABEL band.service.def_position="3x3"

ENV HOST=0.0.0.0
ENV PORT=8080
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE ${PORT}
COPY . .

CMD [ "python", "-m", "debug_test"]
