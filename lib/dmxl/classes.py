#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  dmxl_lib.py
#  
#  Copyright 2013 Eric PASCUAL <eric <at> pobot <dot> org>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  
''' A lightweight Dynamixel bus interface layer '''

import serial

class DynamixelBusInterface(object):
    BROADCASTING_ID = 0xFE
    INTERFACE_ID = 0xFD
    
    """ Model of a Dynamixel bus interfaces accessed though a virtual serial port. 
    
    Unlike other libraries commonly available, we don't add a model layer for 
    representing the servos as instances, since they are pretty straightforward objects
    which don't deserve adding an extra overhead just for wrapping the access to their 
    registers and presenting them as properties.
    
    Use PyDynamixel (http://code.google.com/p/pydynamixel/) for instance if you 
    look for this kind of interface.  
    
    Based on the the standard Robotis USB2Dynamixel, so you can instantiate 
    it for this interface, but it's better to use the USB2Dynamixel sub-class, since
    it defaults the port properly.
    """

    def __init__(self, port, baudrate=1000000, timeout=0.1, debug=False, simulate=False):
        """
        Constructor.
        
        Defaults values for parameters are OK for most of the out of the box
        interfaces, using the bus at its maximum speed. 
        """
        self._serial = serial.Serial(port, baudrate, timeout=timeout)
        self._serial.flushInput()
        self._serial.flushOutput()
        self._debug = debug or simulate
        self._simulate = simulate
        
    def write(self, data):
        """ Writes data to the bus.
        
        Parameters:
            data:
                a list or a string containing the data to be sent
        """
        if isinstance(data, list):
            # stringify a byte list
            data = ''.join([chr(b) for b in data])
            
        if self._debug:
            print(':Tx> %s' % ' '.join('%02x' % ord(b) for b in data))
            
        if self._simulate: 
            return
        
        self._serial.write(data)
        self._serial.flush()
        
    def read(self, count=1):
        """ Reads a given number of bytes from the bus.
        
        See pyserial.Serial class for details about the behavior of the 
        read() method with respect to timeout settings.
        
        Parameters:
            count:
                the count of bytes to be read
        
        Returns:
            the read data as a string, or None if timeout set and exhausted
        """
        return self._serial.read(count)
    
    def get_reply(self, dmxlid):
        """ Awaits for a servo reply and returns its payload and error status.
        
        Parameters:
            dmxlid:
                the expected servo id in the reply
        
        Returns:
            a tuple containing the payload of the reply as a byte list and the error status
        """
        if self._simulate:
            print ('<Rx: -- no Rx data when running in simulated I/O mode --')
            return [],0
        
        hdr = self._serial.read(2)
        if hdr != '\xff\xff':
            self._serial.flushInput()
            raise RuntimeError('invalid reply start : %s' % [ord(b) for b in hdr])
        rcvid = ord(self._serial.read(1)) 
        if rcvid != dmxlid:
            self._serial.flushInput()
            raise RuntimeError('id mismatch: rcv=%d exp=%d' % (rcvid, dmxlid))
        datalen = ord(self._serial.read(1)) - 2
        err = ord(self._serial.read(1))
        data = [ord(c) for c in self._serial.read(datalen)] if datalen else []
        chk = ord(self._serial.read(1))
        if self._debug:
            rx = ' '.join('%02x' % b for b in [0xff, 0xff, rcvid, datalen+2, err] + data + [chk]) 
            print('<Rx: %s' % rx)
        self._serial.flushInput()
        return data, err
    
    def _checksum(self, data):
        """ Computes the checksum of a data buffer."""
        chksum = 0
        for m in data:
            chksum += m
        chksum = ( ~chksum ) % 256
        return chksum
    
    def _check_error(self, err):
        """ Checks an error status value and raises an exception if not ok"""
        if err:
            raise RuntimeError('instruction failed with status=%s' % StatusMask.as_str(err))
        
    def write_instruction(self, dmxlid, instruction):
        """ Sends an instruction and waits for its reply (if not a broadcast).
        
        Parameters:
            dmxlid:
                the target servo id or the broadcast id
            instruction:
                the instruction as a byte list
                
        Returns:
            the received reply as a byte list or nothing for a broadcast
            
        Raises:
            RuntimeError if the received error status is not OK
        """
        _bytes = [0xff, 0xff, dmxlid, len(instruction)+1] + instruction
        chk = self._checksum(_bytes[2:])
        self.write(_bytes + [chk])
        if dmxlid == DynamixelBusInterface.BROADCASTING_ID:
            return
        
        reply, err = self.get_reply(dmxlid)
        self._check_error(err)
        return reply
    
    def read_register(self, dmxlid, reg):
        """ Reads a register from a given servo.
        
        Parameters:
            dmxlid:
                the servo id
            reg:
                the register address
                
        Returns:
            the register value

        Raises:
            ValueError if asking to read from the broadcasting id
        """
        if dmxlid == self.BROADCASTING_ID:
            raise ValueError('id cannot be broadcast one for a read')

        sz = Register.size(reg)
        inst = [Instruction.READ_DATA, reg, sz]
        data = self.write_instruction(dmxlid, inst)
        if sz == 1:
            return data[0]
        else:
            return data[0] + (data[1] << 8)

    def read_intf_register(self, reg):
        """ Reads a register belonging to the interface itself.

        By default, this is just a shorthand for the normal register read,
        but passing the interface id as the servo one. Sub-classes can 
        override it to add some checking (for instance registers not
        defined for the interface)
        """
        return self.read_register(self.INTERFACE_ID, reg)
        
    def write_register(self, dmxlid, reg, value, immed=True):
        """ Writes a register to a given servo.
        
        Parameters:
            dmxlid:
                the servo id
            reg:
                the register address
            value:
                the register value
            immed:
                if True (default), an immediate write is used, otherwise
                a reg_write
                
        Raises:
            ValueError:
                if the value is outside the allowed range for the register
                if the register is read-only
        """
        if not Register.is_writeable(reg):
            raise ValueError('read-only register (%d)' % reg)
        Register.check_value(reg, value)
        
        inst = [Instruction.WRITE_DATA if immed else Instruction.REG_WRITE, 
                reg, value & 0xff]
        if Register.size(reg) != 1:
            inst.append(value >> 8)
        self.write_instruction(dmxlid, inst)

    def write_intf_register(self, reg, value):
        """ Same as read_intf_register but for writing."""
        self.write_register(self.INTERFACE_ID, reg, value)
    def reg_write_register(self, dmxlid, reg, value):
        """ Writes a register in registered (ie delayed) mode.
        
        Shorthand for write_register(dmxlid, reg, value, immed=False)
        """ 
        self.write_register(dmxlid, reg, value, False)
        
    def write_registers(self, dmxlid, reg_start, values, immed=True):
        """ Writes a set of contiguous registers to a given servo.
        
        ..note:
            No checking is done before sending the instruction for involved 
            registers write access and value range validity, as done in
            single writes. If the resulting instruction is invalid, this
            will trigger an error return status from the servo.
        
        Parameters:
            dmxlid:
                the servo id
            reg_start:
                the address of the first register to be written
            values:
                an iterable containing the values of the registers
            immed:
                if True (default), an immediate write is used, otherwise
                a reg_write
                
        Raises:
            ValueError:
                if values parameter is not iterable
        """
        reg = reg_start
        _bytes = []
        for val in values:
            _bytes.append(val & 0xff)
            sz = Register.size(reg)
            if sz == 2:
                _bytes.append((val >> 8) & 0xff)
            reg += sz
            
        try:
            self.write_instruction(dmxlid, [Instruction.WRITE_DATA if immed else Instruction.REG_WRITE, 
                                           reg_start] + _bytes)
        except TypeError:
            raise ValueError('values parameter must be iterable') 

    def reg_write_registers(self, dmxlid, reg_start, values):
        """ Writes a set of contiguous registers to a given servo in delayed mode.
        
        Shorthand for write_registers(dmxlid, reg_start, values, immed=False)
        """
        self.write_registers(dmxlid, reg_start, values, False)
        
    def action(self):
        """ Executes all pending registered writes."""
        self.write_instruction(self.BROADCASTING_ID, [Instruction.ACTION])
    
    def ping(self, dmxlid):
        """ Pings a given servo.
        
        Parameters:
            dmxlid:
                the id of the servo to ping
                
        Returns:
            True if replied, False otherwise
        """
        try:
            self.write_instruction(dmxlid, [Instruction.PING])
            return True
        except:
            return False
        
    def sync_write(self, reg_start, data):
        """ Synchronous write of a set of contiguous registers to a set of servos.
        
        Data to be written must be provided as a collection of tuples, each one
        containing the id of the target servos and the values to be written into
        the registers, starting from reg_start. Register values must themselves be
        a collection of values, all value collections being of the same length of
        course (will raise a ValueError otherwise). 
        
        Beware when using tuples as collections that single item ones must include 
        a comma before the closing paren, otherwise they will be considered as a scalar. 
        
        ..note:
            As for multiple writes, no individual checking is done for the write access
            of involved registers and for the compliance of provided values with allowed
            ranges 
        
        Example:
            # writes registers ReturnDelay, CWAngleLimit and CCWAngleLimit for servos
            # with ids 1, 2 and 3
            
            bus.sync_write(
                dmxl_lib.Register.ReturnDelay,
                ( 
                    (1, (0, 0x10, 0x200)), 
                    (2, (0, 0x20, 0x170)), 
                    (3, (0x10, 0x30, 0x150)) 
                ) 
            )
          
        Parameters:
            reg_start:
                the address of the first register to be written
            data:
                the data to be written.
                
        Raises:
            ValueError if data parameter has not the expected structure
        """
        if not hasattr(data, '__iter__'):
            raise ValueError('data must be iterable')
        
        _, vals0 = data[0]
        try:
            regcnt = len(vals0)
        except TypeError:
            raise ValueError('write data must be iterable')
        reg = reg_start
        regsz = []
        for _ in vals0:
            sz = Register.size(reg)
            reg += sz
            regsz.append(sz)
         
        inst = [Instruction.SYNC_WRITE, reg_start, reg - reg_start]
        for dmxlid, vals in data:
            try:
                if len(vals) != regcnt:
                    raise ValueError('value list size mismatch')
            except TypeError:
                raise ValueError('reg values must be iterable')
            
            inst.append(dmxlid)
            for val, sz in zip(vals, regsz):
                inst.append(val & 0xff)
                if sz == 2:
                    inst.append((val >> 8) & 0xff)
                    
        self.write_instruction(self.BROADCASTING_ID, inst)
    
    def scan(self, first=1, last=253):
        """ Scans the bus to find available servos.
        
        Parameters:
            first, last:
                the bounds of the id range to explore. By default,
                scans the maximum possible range, which can take a bit if time.
                Specify real bounds will speed up things a lot.
        
        Returns:
            the list of the ids of found servos
        """ 
        saved_timeout = self._serial.getTimeout()
        self._serial.setTimeout(0.05)
        try:
            return [dmxlid for dmxlid in range(first, last+1) if self.ping(dmxlid)]
                
        finally:
            self._serial.setTimeout(saved_timeout)
    
    def dump_regs(self, dmxlid):
        """ Dumps all registers of a given target in a user friendly format.
        
        Parameters:
            dmxlid:
                id of the target servo (or interface)
        """
        for reg in Register._meta.iterkeys():
            v = self.read_register(dmxlid, reg)
            Register.dump(reg, v)

class Instruction(object):
    """ A static class defining symbolic names for instructions."""
    PING = 1
    READ_DATA = 2
    WRITE_DATA = 3
    REG_WRITE = 4
    ACTION = 5
    RESET = 6
    SYNC_WRITE = 0x83

    
class USB2Dynamixel(DynamixelBusInterface):
    """ The USB2Dynamixel interface, with appropriate defaults for the constructor."""
    
    def __init__(self, port='/dev/ttyUSB0', **kwargs):
        DynamixelBusInterface.__init__(self, port, **kwargs)

class USB2AX(DynamixelBusInterface):
    """ Xevel's USB2AX v3.x interface.
    
    It adds some extra features, such as the SYNC_READ.
    
    See https://paranoidstudio.assembla.com/wiki/show/paranoidstudio/USB2AX for details
    """
    
    class Instruction(Instruction):
        """ Instruction set specific extension. """
        BOOTLOADER = 8
        SYNC_READ = 0x84

    def __init__(self, port='/dev/ttyACM0', **kwargs):
        DynamixelBusInterface.__init__(self, port, **kwargs)
    
    def read_intf_register(self, reg):
        if reg > Register.Id:
            raise ValueError('reg %d (%s) is not defined for interface' % (reg,
                Register.label(reg)))
        return self.read_register(reg)

    def write_intf_register(self, reg, value):
        raise RuntimeError('interface registers are read-only')

    def sync_read(self, dmxlids, reg):
        """ Reads a register from several servos in one command.
        
        Parameters:
            dmxlids:
                the list of servo ids
            reg:
                the register to be read
        
        Returns:
            the list of register values
        """
        regsize = Register.size(reg)
        inst = [self.Instruction.SYNC_READ, reg, regsize] + dmxlids
        reply = self.write_instruction(self.INTERFACE_ID, inst)
        
        # assemble the returned value set depending of the register size
        if regsize == 1:
            return reply
        else:
            return [reply[i] + (reply[i+1] << 8) for i in range(0, len(reply), 2)]
    

    
class StatusMask(object):
    """ The masks for the error status byte. """
    InstructionError = 1 << 6
    OverloadError = 1 << 5
    ChecksumError = 1 << 4
    RangeError = 1 << 3
    OverheatingError = 1 << 2
    AngleLimitError = 1 << 1
    InputVoltageError = 1
    
    @staticmethod
    def as_str(err):
        res = []
        for s in [s for s in dir(StatusMask) if not s.startswith('_')]:
            attr = getattr(StatusMask, s)
            if type(attr) is int and attr & err:
                res.append(s)
                
        return ','.join(res)
    

class Register(object):
    """ The Dynamixel servos registers base set. """    
    ModelNumber =  0
    FirmwareVersion =  2
    Id = 3
    BaudRate =  4
    ReturnDelay =  5
    CWAngleLimit =  6
    CCWAngleLimit =  8
    TemperatureLimit =  11
    LowVoltageLimit =  12
    HighVoltageLimit =  13
    MaxTorque =  14
    StatusReturnLevel =  16
    AlarmLED =  17
    AlarmShutdown =  18
    DownCalibration =  20
    UpCalibration =  22
    TorqueEnable =  24
    LED =  25
    CWComplianceMargin =  26
    CCWComplianceMargin =  27
    CWComplianceSlope =  28
    CCWComplianceSlope =  29
    GoalPosition = 30
    MovingSpeed = 32
    TorqueLimit =  34
    CurrentPosition =  36
    CurrentSpeed =  38
    CurrentLoad =  40
    CurrentVoltage =  42
    CurrentTemperature =  43
    RegisteredInstruction =  44
    Moving =  46
    Lock =  47
    Punch =  48
    
    _meta = {
        ModelNumber : ("Model Number", 2, False),
        FirmwareVersion : ("Firmware Version", 1, False),
        Id : ("Id", 1, True, 0, 0xfd),
        BaudRate : ("Baud Rate", 1, True, 0, 0xfe),
        ReturnDelay : ("Return Delay", 1, True, 0, 0xfe),
        CWAngleLimit : ("CW Angle Limit", 2, True, 0, 0x3ff),
        CCWAngleLimit : ("CCW Angle Limit", 2, True, 0, 0x3ff),
        TemperatureLimit : ("Temperature Limit", 1, True, 0, 0x96),
        LowVoltageLimit : ("Low Voltage Limit", 1, True, 0x32, 0xfa),
        HighVoltageLimit : ("High Voltage Limit", 1, True, 0x32, 0xfa),
        MaxTorque : ("Max Torque", 2, True, 0, 0x3ff),
        StatusReturnLevel : ("Status Return Level", 1, True, 0, 2),
        AlarmLED : ("Alarm Led", 1, True, 0, 0x7f),
        AlarmShutdown : ("Alarm Shutdown", 1, True, 0, 0x7f),
        DownCalibration : ("Down Calibration", 2, False),
        UpCalibration : ("Up Calibration", 2, False),
        TorqueEnable : ("Torque Enable", 1, True, 0, 1),
        LED : ("LED", 1, True, 0, 1),
        CWComplianceMargin : ("CW Compliance Margin", 1, True, 0, 0xfe),
        CCWComplianceMargin : ("CCW Compliance Margin", 1, True, 0, 0xfe),
        CWComplianceSlope : ("CW Compliance Slope", 1, True, 0, 0xfe),
        CCWComplianceSlope : ("CCW Compliance Slope", 1, True, 0, 0xfe),
        GoalPosition : ("Goal Position", 2, True, 0, 0x3ff),
        MovingSpeed : ("Moving Speed", 2, True, 0, 0x3ff),
        TorqueLimit : ("Torque Limit", 2, True, 0, 0x3ff),
        CurrentPosition : ("Current Position", 2, False),
        CurrentSpeed : ("Current Speed", 2, False),
        CurrentLoad : ("Current Load", 2, False),
        CurrentVoltage : ("Current Voltage", 1, False),
        CurrentTemperature : ("Current Temperature", 1, False),
        RegisteredInstruction : ("Registered Instruction", 1, True, 0, 1),
        Moving : ("Moving", 1, False),
        Lock : ("Lock", 1, True, 1, 1),
        Punch : ("Punch", 2, True, 0, 0x3ff)
    }    

    # _meta tuple field indexes
    _m_label = 0
    _m_size = 1
    _m_writeable = 2
    _m_minval = 3
    _m_maxval = 4
    
    _decoder = {}
     
    @classmethod
    def label(cls, reg):
        return cls._meta[reg][cls._m_label]
    
    @classmethod
    def size(cls, reg):
        return cls._meta[reg][cls._m_size]
    
    @classmethod
    def is_writeable(cls, reg):
        return cls._meta[reg][cls._m_writeable]
    
    @classmethod
    def check_value(cls, reg, value):
        regmeta = cls._meta[reg]
        if not regmeta[cls._m_minval] <= value <= regmeta[cls._m_maxval]:
            raise ValueError('range error (reg=%s value=%d)' % (reg, value))
        
    @classmethod
    def check_id(cls, reg):
        if not reg in cls._meta:
            raise ValueError('invalid register id (%d)' % reg)
    
    @classmethod
    def dump(cls, reg, value):
        try:
            disp_value = cls._decoder[reg](value)
        except KeyError:
            disp_value = str(value)
        print ('- [%02d] %-30s : %s (0x%0.2x)' % (reg, cls.label(reg), disp_value, value))


BAUDRATE = {
    1: 1000000,
    3: 500000,
    4: 400000,
    7: 250000,
    9: 200000,
    16: 115200,
    34: 57600,
    103: 19200,
    207:9600
}

def _decode_baudrate(value):
    return BAUDRATE[value]

STATUS_LEVEL = {
    0: 'no_reply',
    1: 'read_data_only',
    2: 'all'
}

def _decode_status_level(value):
    return STATUS_LEVEL[value]

def _decode_error_status(value):
    return StatusMask.as_str(value)

def _decode_reginst(value):
    return 'yes' if value else 'no'


Register._decoder = {
    Register.BaudRate : _decode_baudrate,
    Register.StatusReturnLevel : _decode_status_level,
    Register.AlarmLED : _decode_error_status,
    Register.AlarmShutdown : _decode_error_status,
    Register.RegisteredInstruction : _decode_reginst
}

