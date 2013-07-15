#!/usr/bin/env python

"""
Interface for using a I2C LCD (mod. LCD03) from Robot Electronics.

See http://www.robot-electronics.co.uk/acatalog/LCD_Displays.html

Based on documentation available at :
http://www.robot-electronics.co.uk/htm/Lcd03tech.htm
"""

import string
import threading
import time

__author__ = "Eric Pascual"
__email__ = "eric@pobot.org"
__copyright__ = "Copyright 2012, POBOT"
__version__ = "1.0"
__date__ = "Dec. 2012"
__status__ = "Development"
__license__ = "LGPL"

_keymap = '123456789*0#'

class LCD03(object):
    """ Provides the interface for a LCD03 device. """

    # default address (7 bits format => eq. 0xC6)
    DFLT_ADDR = 0x63

    # registers
    REG_CMD = 0            # write
    REG_FIFO_FREE = 0      # read
    REG_KEYPAD_LOW = 1     # read
    REG_KEYPAD_HIGH = 2    # read
    REG_VER = 3            # read

    # commands
    CMD_HOME = 1
    CMD_SET_CURSOR_POS = 2
    CMD_SET_CURSOR_LC = 3
    CMD_CURSOR_INVISIBLE = 4
    CMD_CURSOR_UL = 5
    CMD_CURSOR_BLINK = 6
    CMD_BACKSPACE = 7
    CMD_HTAB = 9
    CMD_DOWN = 10
    CMD_UP = 11
    CMD_CLEAR = 12
    CMD_CR = 13
    CMD_CLEAR_COL = 17
    CMD_TAB_SET = 18
    CMD_BACKLIGHT_ON = 19
    CMD_BACKLIGHT_OFF = 20
    CMD_STARTMSG_OFF = 21
    CMD_STARTMSG_ON = 22
    CMD_ADDR_CHANGE = 25
    CMD_CUSTOM_CHARGEN = 27
    CMD_KPSCAN_FAST = 28
    CMD_KPSCAN_NORMAL = 29

    # cursor types
    CT_INVISIBLE = 0
    CT_UNDERLINE = 1
    CT_BLINK = 2

    def __init__(self, bus, addr=DFLT_ADDR, height=4, width=20, debug=False):
        """ Constructor.

        Arguments:
            bus: 
                an I2CBus/SMBus instance representing the bus this device is
                connected to
            addr:
                the I2C device address (in 7 bits format)
            height:
                the number of lines of the LCD
            width:
                the number of character per line of the LCD
        """
                    
        self._debug = debug
        
        self._bus = bus
        self._addr = addr
        self._height = height
        self._width = width

        self._scan_thread = None
        
        # this lock is used to avoid issuing a command while the LCD is not ready
        # (some display operations can be lengthy)
        self._lock = threading.Lock()
        
    def __del__(self):
        """ Destructor.
        
        Ensures the keypad scanning thread is not left hanging if any.
        """
        self.keypad_autoscan_stop()

    @property
    def height(self):
        """ The LCD height, as its number of lines. """
        return self._height

    @property
    def width(self):
        """ The LCD width, as its number of characters per line. """
        return self._width

    def get_version(self):
        """ Returns the firmware version. """
        return self._bus.read_byte_data(self._addr, self.REG_VER)

    def clear(self):
        """ Clears the display and move the cursor home. """
        with self._lock:
            self._bus.write_byte_data(self._addr, self.REG_CMD, self.CMD_CLEAR)
            time.sleep(0.1)
        
    def home(self):
        """ Moves the cursor home (top left corner). """
        self._bus.write_byte_data(self._addr, self.REG_CMD, self.CMD_HOME)

    def goto_pos(self, pos):
        """ Moves the cursor to a given position.

        Arguments:
            pos:
                the position (between 1 and height * width)
        """
        self._bus.write_block_data(self._addr, self.REG_CMD, 
                [self.CMD_SET_CURSOR_POS, pos])

    def goto_line_col(self, line, col):
        """ Moves the cursor to a given position.

        Arguments:
            line:
                the line number (between 1 and height)
            col:
                the column number (between 1 and width)
        """
        self._bus.write_block_data(self._addr, self.REG_CMD, 
                [self.CMD_SET_CURSOR_LC, line, col])

    def write(self, s):
        """ Writes a text at the current position.

        Argument:
            s:
                the text (max length : 32)
        """
        with self._lock:
            self._bus.write_block_data(self._addr, self.REG_CMD,
                    [ord(c) for c in s[:32]])
            time.sleep(0.1)

    def backspace(self):
        """ Moves the cursor one position left and erase the character there. """
        self._bus.write_byte_data(self._addr, self.REG_CMD, self.CMD_BACKSPACE)

    def htab(self):
        """ Moves the cursor to the next tabulation. """
        self._bus.write_byte_data(self._addr, self.REG_CMD, self.CMD_HTAB)

    def move_down(self):
        """ Moves the cursor one position downwards. """
        self._bus.write_byte_data(self._addr, self.REG_CMD, self.CMD_DOWN)

    def move_up(self):
        """ Moves the cursor one position upwards. """
        self._bus.write_byte_data(self._addr, self.REG_CMD, self.CMD_UP)

    def cr(self):
        """ Moves the cursor to the line start. """
        self._bus.write_byte_data(self._addr, self.REG_CMD, self.CMD_CR)

    def clear_column(self):
        """ Clears the column at the cursor position. """
        self._bus.write_byte_data(self._addr, self.REG_CMD, self.CMD_CLEAR_COL)

    def tab_set(self, pos):
        """ Defines a tabulation position.

        Arguments:
            pos:
                the position (between 1 and 11)
        """
        if pos in range(1, 11):
            self._bus.write_block_data(self._addr, self.REG_CMD, 
                    [self.CMD_TAB_SET, pos])

    def set_backlight(self, on):
        """ Controls the backlight.

        Arguments:
            on:
                True to turn the backlight on, False to turn it off
        """
        self._bus.write_byte_data(self._addr, self.REG_CMD, 
                self.CMD_BACKLIGHT_ON if on else self.CMD_BACKLIGHT_OFF)

    def set_startup_message(self, on):
        """ Controls the display of the startup message.

        Arguments:
            on:
                True to display the message, False to hide it
        """
        self._bus.write_byte_data(self._addr, self.REG_CMD, 
                self.CMD_STARTMSG_ON if on else self.CMD_STARTMSG_OFF)

    def set_cursor_type(self, ct):
        """ Controls the cursor type.

        Arguments:
            ct:
                The cursor type (CT_INVISIBLE, CT_UNDERLINE, CT_BLINK)
        """
        if ct in range(3):
            self._bus.write_byte_data(self._addr, self.REG_CMD, 
                    self.CMD_CURSOR_INVISIBLE + ct)

    def get_keypad_state(self):
        """ Returns the keypad state, as a bit field. """
        data = self._bus.read_block_data(self._addr, self.REG_KEYPAD_LOW, 2)
        
        try:
            return (data[1] << 8) + data[0]
        except:
            # be fault tolerant in case of I/O problem
            return 0

    @staticmethod
    def state_to_keys(state):
        """ Converts a keypad state bit field into the corresponding
        list of keys. """
        keys = []
        for k in _keymap:
            if state & 1:
                keys.append(k)
            state >>= 1
        return keys

    def get_keys(self):
        """ Returns the list of keys currently pressed on the keypad. """
        return self.state_to_keys(self.get_keypad_state())
    
    def hsep(self, line=None, pattern='-'):
        """Draw an horizontal separator across the display.
        
        Arguments:
            line:
                the line on which the separator is drawn. 
                default: the current one.
            pattern:
                the pattern to be used for the line
                default: '-'
        """
        s = (pattern * self._width)[:self._width]
        if line and line in range(1, self._height + 1):
            self.goto_line_col(line, 1)
        else:
            self.cr()
        self.write(s)
        
    def write_at(self, s, line, col):
        """ Convenience method to write a text at a given location.
        
        Arguments:
            s: 
                the text
            line, col:
                the text position
        """
        self.goto_line_col(line, col)
        self.write(s)
        
    def center_text_at(self, s, line):
        """ Convenience method to write a centered text on a given line.
        
        Arguments:
            s: 
                the text
            line:
                the text line
        """
        self.write_at(string.center(s, self._width), line, 1)
        
    def keypad_autoscan_start(self, callback):
        """ Starts the automatic keypad scan.
        
        Does nothing if already active.
        
        Arguments:
            callback:
                a callable to be invoked when a keypad state change has
                been detected. The callable will be passed the array of
                pressed keys and the instance of the LCD as arguments. So
                it must be defined as def ...(keys, lcd)
                
        Returns:
            True if started, False if already running
                
        Exceptions:
            ValueError:
                if callback argument is not a valid callable
        """
        if self._scan_thread:
            return False
        
        if not callable(callback):
            raise ValueError('callback is not a valid callable')

        # always work in fast scan        
        self._bus.write_byte_data(self._addr, self.REG_CMD, self.CMD_KPSCAN_FAST) 
        
        self._scan_thread = threading.Thread(None, self._keypad_scanner, name='scanner', args=(callback,))
        self._scan_keypad = True
        self._scan_thread.start()
        return True

    def keypad_autoscan_stop(self):
        """ Stops the keypad autoscan if active. 

        Returns:
            True if stopped, False if not already running
                
        """
        if self._scan_thread:
            self._scan_keypad = False
            self._scan_thread = None
            return True
        else:
            return False

    def _keypad_scanner(self, callback):
        """ Internal method used to scan the keypad. Not to be called directly by externals. """
        last_keys = None
        while self._scan_keypad:
            with self._lock:
                keys = self.get_keys()

            if keys and keys != last_keys:
                callback(keys, self)

            last_keys = keys
            time.sleep(0.1)


