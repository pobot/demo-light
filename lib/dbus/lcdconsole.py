import dbus.service

from pybot.lcd03 import LCD03
import pybot.log
import time
import threading

# I2C_BUS_ID = 1

BUSNAME = 'org.pobot.rob.Console'
IF_DISPLAY = 'org.pobot.rob.Console.display'
IF_INPUT = 'org.pobot.rob.Console.input'
IF_CONTROL = 'org.pobot.rob.Console.control'
OBJPATH = '/org/pobot/rob/Console/object'

_logger = pybot.log.getLogger('console')

class ConsoleService(dbus.service.Object):
    _loop = None

    def __init__(self, i2c_bus, dbus_bus, dbus_loop):
        self._loop = dbus_loop

        self._lcd = LCD03(i2c_bus)
        self._lcd.set_cursor_type(LCD03.CT_INVISIBLE)

        self._scan_thread = None
        self._menu = None

        connection = dbus.service.BusName(BUSNAME, bus=dbus_bus)
        dbus.service.Object.__init__(self, connection, OBJPATH)

        _logger.info('started')

    @dbus.service.method(IF_DISPLAY)
    def clear(self):
        self._lcd.clear()
        self._menu = None

    @dbus.service.method(IF_DISPLAY)
    def home(self):
        self._lcd.home()

    @dbus.service.method(IF_DISPLAY, in_signature='b')
    def set_backlight(self, on):
        self._lcd.set_backlight(on)

    @dbus.service.method(IF_DISPLAY, in_signature='suu')
    def write_at(self, s, line, col):
        self._lcd.write_at(s, line, col)

    @dbus.service.method(IF_DISPLAY, in_signature='su')
    def center_text_at(self, s, line):
        self._lcd.center_text_at(s, line)

    @dbus.service.method(IF_DISPLAY)
    def show_splash(self):
        self._lcd.clear()
        self._lcd.center_text_at('DroidBuster v1.0', 1)
        self._lcd.center_text_at('-**-', 2)
        
    @dbus.service.method(IF_DISPLAY, in_signature='ssas')
    def display_menu(self, menu_id, title, options):
        optcnt = len(options)
        if not 0 < optcnt < 7:
            raise ValueError('invalid option count (%d)' % optcnt)
        
        self._lcd.clear()
        self._lcd.center_text_at(title, 1)
        col = 1
        offs = 2
        colw = 18 if optcnt < 4 else 7
        for i, s in enumerate(options):
            if i == 3:
                offs, col = -1, 12
            self._lcd.write_at('%d.%s' % (i + 1, s[:colw]), i + offs, col)
        self._menu = (menu_id, optcnt)
        _logger.info('displaying menu: %s' % str(self._menu))
        
        self.listen_to_keypad(True)
        
    @dbus.service.method(IF_INPUT, out_signature='as')
    def get_keys(self):
        return self._lcd.get_keys()

    @dbus.service.signal(IF_INPUT, signature='as')
    def key_pressed(self, keys):
        pass

    @dbus.service.signal(IF_INPUT, signature='si')
    def option_selected(self, menu_id, option):
        _logger.info("option '%d' selected in menu '%s'" % (option, menu_id))
        if option < 4:
            col, line = 2, option + 1
        else:
            col, line = 13, option - 2
        self._lcd.write_at('>', line, col)
        self._menu = None

    @dbus.service.method(IF_CONTROL, in_signature='b')
    def listen_to_keypad(self, state):
        if state:
            if self._lcd.keypad_autoscan_start(self._autoscan_callback):
                _logger.info('listening to keypad')
        else:
            if self._lcd.keypad_autoscan_stop():
                _logger.info('no more listening to keypad')

    def _autoscan_callback(self, keys, _lcd):
        if self._menu:
            menu_id, optcnt = self._menu
            try:
                opt = int(keys[0])
                if opt in range(1, optcnt + 1):
                    self.option_selected(menu_id, opt)
                    self.listen_to_keypad(False)
                    self._selected_option = opt
            except:
                pass
            
        else:
            self.key_pressed(keys)

    def run(self):
        if self._loop:
            _logger.info('running')
            self._loop.run()
            
            _logger.info('terminating')
            self.listen_to_keypad(False)
            self._lcd.set_backlight(False)

    @dbus.service.method(IF_CONTROL)
    def shutdown(self):
        if self._loop:
            self._loop.quit()

