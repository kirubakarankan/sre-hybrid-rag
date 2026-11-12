PY = .venv/bin/python

setup:
	python3.13 -m venv .venv
	$(PY) -m pip install -r requirements.txt

corpus:
	git clone --depth 1 https://github.com/prometheus-operator/runbooks data/runbooks

ingest:
	$(PY) ingest.py data/runbooks/content/runbooks

test:
	$(PY) -m pytest -q

index:
	$(PY) search.py index

eval:
	$(PY) -m evals.run_evals
