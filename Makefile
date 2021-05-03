#!/usr/bin/env make

# this loads $(ENV_FILE) as both makefile variables and into shell env
ENV_FILE?=.env
include $(ENV_FILE)
export $(shell sed 's/=.*//' $(ENV_FILE))

.PHONY:  deps black docs

deps:
	./dependencies.py

black:
	black examples pytimings tests

docs:
	make -C docs html
