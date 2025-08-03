# Simple Makefile for validation and release helpers

.PHONY: install-dev test validate pre-release

# Use the project venv by default
PY?=.venv/bin/python
PIP?=.venv/bin/pip
PYTEST?=.venv/bin/pytest

install-dev:
	$(PY) -m ensurepip --upgrade || true
	$(PIP) install -U pip
	$(PIP) install -U pytest pytest-asyncio
	$(PIP) install -e .

test:
	$(PYTEST) -q

validate: test
	scripts/validate.py

pre-release: validate
	@echo "Validation passed. Ready to build and publish."
