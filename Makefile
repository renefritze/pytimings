#!/usr/bin/env make

# this loads $(ENV_FILE) as both makefile variables and into shell env
ENV_FILE?=.env
include $(ENV_FILE)
export $(shell sed 's/=.*//' $(ENV_FILE))

.PHONY: deps format docs

deps:
	uv sync --extra ci

format:
	uv run ruff format pytimings tests

docs:
	make -C docs html
