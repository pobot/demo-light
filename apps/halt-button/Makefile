# Makefile for the creation of the Debian deployment package.

# Dependencies:
# - rsync
# - dpkg-deb

SHELL=/bin/bash

APP_NAME=halt-button

VERSION?=$(shell grep -e '^Version:' DEBIAN/control | cut -d' ' -f2 | tr -d [:blank:])
DEBPKG_NAME?=$(APP_NAME)_$(VERSION)_all

RSYNC=rsync -Ca

REMOTE=raspberrypi.local

BUILD_ROOT=build
BUILD_USR_LOCAL_BIN=$(BUILD_ROOT)/usr/local/bin
BUILD_INIT_D=$(BUILD_ROOT)/etc/init.d

dist: update_build_tree
	@echo '------ creating Debian package...'
	fakeroot dpkg --build $(BUILD_ROOT) $(DEBPKG_NAME).deb

update_build_tree: 
	@echo '------ copying files in build area...'
	mkdir -p $(BUILD_USR_LOCAL_BIN) $(BUILD_INIT_D)

	# dpkg files
	cp -ar DEBIAN $(BUILD_ROOT)

	# application scripts
	cp -ar usr/local/bin/*.py $(BUILD_USR_LOCAL_BIN)
	
	# init script
	cp -a etc/init.d/$(APP_NAME) $(BUILD_INIT_D)

clean:
	@echo '------ cleaning all...'
	rm -rf $(BUILD_ROOT) $(DEBPKG_NAME).deb

deploy: dist
	scp $(DEBPKG_NAME).deb pi@$(REMOTE):

.PHONY: dist deploy clean update_build_tree
