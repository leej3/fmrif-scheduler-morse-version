#!/bin/bash

set -e

fatal() {
	echo "$@" 1>&2
	exit 2
}

if ! test -f 003-import-data.sql; then
	fatal "missing 003-import-data.sql (data only dump from original database, not included in repo)"
fi

dropdb --if-exists scheduler
createdb scheduler --encoding=UTF-8 --lc-collate=C.UTF-8 --lc-ctype=C.UTF-8 --template=template0

for sql in $(echo "[0-9][0-9][0-9]-*.sql" | sort); do
	echo "=== running: $sql"
	psql -X -q -f "$sql" -d scheduler
done

pg_dump -s -O --no-acl -f new-schema.sql scheduler

./generate-schemapdf.sh
