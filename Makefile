.PHONY: all deps verify audit book covers site kdp clean

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
	python3 book/kdpcheck.py

covers: book
	python3 book/cover.py

site: book
	python3 book/site.py

kdp:
	python3 book/kdpcheck.py

clean:
	rm -rf build site
