'''
I2C base stuff

@author: eric
'''

import serial
import time
import threading
import smbus

class I2CBus(object):
    '''
    Abstract class for I2C interface implementations
    '''

    def __init__(self, debug=False, simulate=False, msb_first=False):
        self.msb_first = msb_first
        self._debug = debug
        self._simulate = simulate

    def read_byte(self, addr):
        raise NotImplementedError()

    def write_byte(self, addr, data):
        raise NotImplementedError()

    def read_byte_data(self, addr, reg):
        raise NotImplementedError()

    def write_byte_data(self, addr, reg, data):
        raise NotImplementedError()

    def read_word_data(self, addr, reg):
        raise NotImplementedError()

    def write_word_data(self, addr, reg, data):
        raise NotImplementedError()

    def read_block_data(self, addr, reg, nbytes):
        raise NotImplementedError()

    def write_block_data(self, addr, reg, data):
        raise NotImplementedError()


class USB2I2CBus(I2CBus):
    """ USB interface for an I2C bus.

    Gives access to an I2C bus via a virtual serial port.

    See http://www.robot-electronics.co.uk/htm/usb_i2c_tech.htm for details
    """
    I2CD_CMD = 0x53
    I2C_CMD = 0x55
    USBI2C_CMD = 0x5A

    def __init__(self, dev, **kwargs):
        """ Constructor.

        Parameters:


        """
        I2CBus.__init__(self, **kwargs)
        self._serial = serial.Serial(dev, baudrate=19200, timeout=0.5)
        self._serial.flushInput()
        self._serial.flushOutput()

        # I/O serialization lock to be as much thread safe as possible
        self._lock = threading.Lock()

    def _send_cmd(self, data):
        if isinstance(data, list):
            # stringify a byte list
            data = ''.join([chr(b) for b in data])

        if self._debug or self._simulate:
            print(':Tx> %s' % ' '.join('%02x' % ord(b) for b in data))
        if self._simulate:
            return
        with self._lock:
            self._serial.write(data)
            self._serial.flush()

    def _get_reply(self, nbytes):
        if self._simulate:
            print ('<Rx: -- no Rx data when running in simulated I/O mode --')
            return []

        with self._lock:
            data = []
            cnt = 0
            maxwait = time.time() + self._serial.timeout
            while cnt < nbytes and time.time() < maxwait:
                data = data + [ord(c) for c in self._serial.read(nbytes - cnt)]
                cnt = len(data)
            self._serial.flushInput()

        if self._debug:
            rx = ' '.join('%02x' % b for b in data)
            print('<Rx: %s' % rx)

        return data

    def read_byte(self, addr):
        self._send_cmd([self.I2CD_CMD, (addr << 1) + 1])
        return self._get_reply(1)[0]

    def write_byte(self, addr, data):
        self._send_cmd([self.I2CD_CMD, addr << 1, data & 0xff])
        result = self._get_reply(1)[0]
        if not result:
            raise RuntimeError('write_byte failed with result=%d' % result)

    def read_byte_data(self, addr, reg):
        return self.read_block_data(addr, reg, 1)[0]

    def write_byte_data(self, addr, reg, data):
        return self.write_block_data(addr, reg, [data])

    def read_word_data(self, addr, reg):
        data = self.read_block_data(addr, reg, 2)
        if self.msb_first:
            return (data[0] << 8) + data[1]
        else:
            return (data[1] << 8) + data[0]

    def write_word_data(self, addr, reg, data):
        if self.msb_first:
            return self.write_block_data(addr, reg,
                                         [(data >> 8) & 0xff, data & 0xff])
        else:
            return self.write_block_data(addr, reg,
                                         [data & 0xff, (data >> 8) & 0xff])

    def read_block_data(self, addr, reg, nbytes):
        self._send_cmd([self.I2C_CMD, (addr << 1) + 1, reg, nbytes])
        return self._get_reply(nbytes)

    def write_block_data(self, addr, reg, data):
        self._send_cmd([self.I2C_CMD, addr << 1, reg, len(data)] + data)
        result = self._get_reply(1)[0]
        if not result:
            raise RuntimeError('write_block_data failed with result=%d' % result)

class SMBusI2CBus(I2CBus):
    """ I2C bus access via SMBus (e.g. RasPi).

    This is just a wrapper of SMBus, diverting xx_block_data
    methods to xx_i2c_block_data, since SMBus and I2C do not
    work the same for block data I/O.

    Sub-class SMBus would have been lighter as an implementation,
    but it is not an acceptable base type
    """

    def __init__(self, bus_id=1, **kwargs):
        I2CBus.__init__(self, **kwargs)
        self._bus = smbus.SMBus(bus_id)
        # I/O serialization lock
        self._lock = threading.Lock()

    def read_byte(self, addr):
        with self._lock:
            return self._bus.read_byte(addr)

    def write_byte(self, addr, data):
        with self._lock:
            self._bus.write_byte(addr, data)

    def read_byte_data(self, addr, reg):
        with self._lock:
            return self._bus.read_byte_data(addr, reg)

    def write_byte_data(self, addr, reg, data):
        with self._lock:
            self._bus.write_byte_data(addr, reg, data)

    def read_word_data(self, addr, reg):
        with self._lock:
            return self._bus.read_word_data(addr, reg)

    def write_word_data(self, addr, reg, data):
        with self._lock:
            self._bus.write_word_data(addr, reg, data)

    def read_block_data(self, addr, reg, nbytes):
        with self._lock:
            return self._bus.read_i2c_block_data(addr, reg, nbytes)

    def write_block_data(self, addr, reg, data):
        with self._lock:
            self._bus.write_i2c_block_data(addr, reg, data)

