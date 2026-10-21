
.PHONY: schema types

PYTHON := ./.venv/bin/python


schema:
	mkdir -p build
	$(PYTHON) manage.py spectacular \
		--file build/openapi-drf.json \
		--format openapi-json \
		--validate
	$(PYTHON) scripts/merge_openapi.py

types: schema
	cd ../web && \
		npx openapi-typescript ../backend/build/openapi.json \
		-o src/lib/api/api-schema.d.ts
