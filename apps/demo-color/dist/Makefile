# Makefile for the creation of the Debian deployment package.

# Dependencies:
# - rsync
# - dpkg-deb

SHELL=/bin/bash

APP_NAME=pobot-demo-color

VERSION?=$(shell grep -e '^Version:' DEBIAN/control | cut -d' ' -f2 | tr -d [:blank:])
DEBPKG_NAME?=$(APP_NAME)_$(VERSION)_all

RSYNC=rsync -Ca

BUILD_ROOT=build
BUILD_OPT=$(BUILD_ROOT)/opt/$(APP_NAME)
BUILD_VAR_LIB=$(BUILD_ROOT)/var/lib/$(APP_NAME)
BUILD_ETC=$(BUILD_ROOT)/etc/$(APP_NAME)
BUILD_INIT_D=$(BUILD_ROOT)/etc/init.d

dist: update_build_tree
	@echo '------ creating Debian package...'
	fakeroot dpkg --build $(BUILD_ROOT) $(DEBPKG_NAME).deb

update_build_tree: 
	@echo '------ copying files in build area...'
	mkdir -p $(BUILD_OPT) $(BUILD_ETC) $(BUILD_INIT_D)

	# dpkg files
	cp -ar DEBIAN $(BUILD_ROOT)

	# application scripts
	$(RSYNC) \
		--filter "-s .*" \
		--include "*/" \
		--include "*.py" \
		--include "*.html" \
		--include "*.js" \
		--include "*.css" \
		--include "*.png" \
		--include "*.jpg" \
		--include "*.jpeg" \
		--include "*.gif" \
		--include "*.svg" \
		--include "*.pdf" \
		--exclude "*" \
		../src/ $(BUILD_OPT)

	# init script
	cp -a ../init.d/$(APP_NAME) $(BUILD_INIT_D)

	# application default configuration
	cp -a ./etc/$(APP_NAME)/* $(BUILD_ETC)

	# third party libraries
	$(RSYNC) \
		--filter "-s .*" \
		--include "*.so" \
		--exclude "*.pyc" \
		--exclude "test/" \
		/usr/local/lib/python2.7/dist-packages/tornado $(BUILD_OPT)


clean:
	@echo '------ cleaning all...'
	rm -rf $(BUILD_ROOT) $(DEBPKG_NAME).deb

