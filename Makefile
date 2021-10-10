help:
	@echo "make all, build, upload, help"

all: build upload

build:
	python3 -m build

upload:
	python3 -m twine upload dist/*

.PHONY: all build upload help
