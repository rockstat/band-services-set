FROM {band-base-py-image}
WORKDIR /usr/src/services

LABEL band.service.version="0.0.1"
LABEL band.service.title="Band service title"
LABEL band.service.def_position="4x0"

ENV HOST=0.0.0.0
ENV PORT=8080
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE ${PORT}
COPY . .

CMD [ "python", "-m", "bandservice"]
