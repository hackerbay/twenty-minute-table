.PHONY: all deps verify book site clean

all: verify book site

deps:
	npm install

verify:
	python3 book/verify.py

book:
	python3 book/build.py
	python3 book/render.py

site: book
	python3 book/site.py

clean:
	rm -rf build site
