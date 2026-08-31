.PHONY: all deps verify audit book covers epub pricing amazon site kdp clean

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

epub: covers
	python3 book/epub.py
	python3 book/epubcheck.py

pricing:
	python3 book/pricing.py

# everything needed to submit to Amazon: interior, wrap, Kindle edition, and the
# margin check — you should not be able to prepare a submission whose economics
# do not work. CI builds the artefacts without this, so a business decision that
# has not been made yet cannot turn the build red.
amazon: verify audit book covers epub pricing

site: book
	python3 book/site.py

kdp:
	python3 book/kdpcheck.py

clean:
	rm -rf build site
