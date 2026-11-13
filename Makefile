PY = .venv/bin/python
# Pinned so the published results stay reproducible when the upstream runbooks change.
CORPUS_COMMIT = a685d14cf5128bb30e2bf935c3983decd772d885

.PHONY: setup corpus ingest index test lint eval lock

setup:
	python3.13 -m venv .venv
	$(PY) -m pip install -r requirements.lock

corpus: data/runbooks
ingest: chunks.jsonl
index: chroma/.indexed

data/runbooks:
	git clone https://github.com/prometheus-operator/runbooks $@
	git -C $@ checkout --quiet $(CORPUS_COMMIT)

chunks.jsonl: data/runbooks ingest.py
	$(PY) ingest.py data/runbooks/content/runbooks

chroma/.indexed: chunks.jsonl search.py
	$(PY) search.py index

test:
	$(PY) -m pytest -q

lint:
	$(PY) -m ruff check .

eval: chroma/.indexed
	$(PY) -m evals.run_evals

# Re-create the full list of exact versions after changing requirements.txt.
lock:
	$(PY) -m pip install -r requirements.txt
	$(PY) -m pip freeze > requirements.lock
