.PHONY: all deps verify audit book site clean

all: verify audit book site

deps:
	npm install

verify:
	python3 book/verify.py

audit:
	python3 book/audit.py

book:
	python3 book/build.py
	python3 book/render.py

site: book
	python3 book/site.py

clean:
	rm -rf build site
