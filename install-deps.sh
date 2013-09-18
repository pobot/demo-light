#!/bin/bash

# Downloads and installs dependencies used by the Pybot library.
#
# Beware that some of them can only be executed on the RasPi (GPIO library for
# instance), and thus cannot be installed on your desktop machine.


function info() {
    echo "[INFO] $*"
}

function warn() {
    echo "[WARN] $*"
}

[[ "$(uname -m)" == arm* ]] && is_raspi=1 || is_raspi=0

info "Fetching SPI-Py..."
wget https://github.com/lthiery/SPI-Py/archive/master.zip -O /tmp/spi-py.zip
info "Installing SPI-Py..."
(cd /tmp && unzip -o spi-py.zip && cd SPI-Py-master && python setup.py install)

info "Fetching RPi.GPIO..."
wget http://raspberry-gpio-python.googlecode.com/files/RPi.GPIO-0.5.3a.tar.gz -P /tmp
info "Installing SPI-Py..."
if [ $is_raspi ] ; then
    (\
        cd /tmp && \
        tar xf RPi.GPIO-0.5.3a.tar.gz && \
        cd RPi.GPIO-0.5.3a && \
        python setup install \
    )
else
    warn "This package can only be installed on the RasPi."
fi

info "Fetching i2c-tools from lm-sensors..."
wget http://dl.lm-sensors.org/i2c-tools/releases/i2c-tools-3.1.0.tar.bz2 -P /tmp
info "Installing i2c-tools..."
if [ $is_raspi ] ; then
    (\
        cd /tmp && \
        tar xf i2c-tools-3.1.0.tar.gz && \
        cd i2c-tools-3.1.0 && \
        make EXTRA="py-smbus" && \
        make install EXTRA="py-smbus"\
    )
else
    warn "This package can only be installed on the RasPi."
fi


