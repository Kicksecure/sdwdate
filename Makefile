#!/usr/bin/make -f

all:
	@echo "make all is not required."

install:
	$(CURDIR)/install-helper.bsh
clean:
	git clean -df

.PHONY: clean install
