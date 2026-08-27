.PHONY: all deps verify build clean

all: verify build

deps:
	npm install

verify:
	python3 book/verify.py

build:
	python3 book/build.py
	python3 book/render.py

clean:
	rm -rf build
