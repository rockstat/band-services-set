bump-patch:
	bumpversion patch

bump-minor:
	bumpversion minor

start-dev:
	@LOG_LEVEL=debug &&  /usr/bin/env python3 -m "$${PWD##*/}"

clean:
	find . -name "*.pyc" -exec rm -f "{}" \;

run-host:
	curl "host:10000/run/$${PWD##*/}" | jq

rm-host:
	curl "host:10000/stop/$${PWD##*/}" -s | jq
	sleep 1
	curl "host:10000/rm/$${PWD##*/}" -s | jq

