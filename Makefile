#!/usr/bin/make -f

all:
	@echo "make all is not required."

install:
	rsync \
		-C \
		--verbose \
		--recursive \
		--links \
		--perms \
		--times \
		--exclude Makefile \
		--exclude man-helper.bsh \
		--exclude man \
		--exclude debian \
		--exclude t \
		--exclude .gitignore \
		--exclude .gitattributes \
		--exclude COPYING \
		--exclude GPLv3 \
		--exclude build \
		--exclude clean \
		--exclude CONTRIBUTING.md \
		$(CURDIR)/ \
		$(DESTDIR)/

clean:
	git clean -df

.PHONY: clean install
