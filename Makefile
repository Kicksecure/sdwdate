#!/usr/bin/make -f

## generic deb build script version 0.3

DESTDIR ?= /

all:
	@echo "make all is not required."

dist:
	./make-helper.bsh dist

manpages:
	./make-helper.bsh manpages

install:
	./make-helper.bsh install

deb-pkg:
	./make-helper.bsh deb-pkg

deb-pkg-install:
	./make-helper.bsh deb-pkg-install

deb-install:
	./make-helper.bsh deb-install

clean:
	./make-helper.bsh clean

distclean:
	./make-helper.bsh distclean

checkout:
	./make-helper.bsh checkout

help:
	./make-helper.bsh help
