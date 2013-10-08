#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" PyGame related classes used for the GUI of beacons_gui application."""

import logging
import math
import time

import pygame

import beacons_gui.utils as utils


class DisplayObject(object):
    """ Root class for graphical objets.

    We could have used pygame sprites, but...
    """
    def draw(self, surface):
        """ Object drawing process, to be implemented by sub-classes.

        Parameters:
            surface:
                the surface on which the object must be drawn
        """
        raise NotImplementedError()


class Beacon(DisplayObject):
    """ Graphical object for representing a beacon.

    The dish part is animated and reflects the real time position as
    provided by the beacon itself.

    In addition, it draws the "ray" when an echo is detected by the sensor.
    """
    SIZE = 100.
    RAY_MAX_AGE = 0.5
    TARGET_HEADING_MAX_AGE = 1

    def __init__(self, location, scan_range,
                 angle_label,
                 ray_color=pygame.Color('green'),
                 ray_length=999,
                 debug=False):
        """ Constructor

        Parameters:
            location:
                (x, y) tuple containing the position of the object center
                on the display
            scan_range:
                tuple containing the bounds (in degrees) of the scan range
            ray_color:
                the color used to draw the ray showing the direction of an echo
                (default: green)
            ray_length:
                the length of the ray
                (default: 999)
            debug:
                internal debuging flag
        """
        self._location = location
        self._scan_range = scan_range
        self._heading = None
        self._target_heading = None
        self._target_heading_when = None
        self._ray_color = ray_color
        self._ray_length = ray_length
        self._ray_when = None
        self._new_echo = False

        self._angle_label_color = pygame.color.Color('orange')
        font = pygame.font.SysFont('monospace', 14, bold=False)
        self._angle_label = font.render(angle_label, True, self._angle_label_color)

        self._log = logging.getLogger('beacon-%s' % angle_label)
        self._log.setLevel(logging.DEBUG if debug else logging.INFO)

        # creates the images used to draw the beacon parts
        self._img_base = pygame.transform.rotozoom(
            self._make_image('beacon-base.png', self.SIZE),
            180,
            1
        )
        self._img_dish = pygame.transform.rotozoom(
            self._make_image('beacon-dish.png', self.SIZE),
            180,
            1
        )
        self._img_hilite = self._make_image('beacon-hilite.png', self.SIZE)

        # setup the bounding rect of the beacon, for mouse interaction
        self._rect = pygame.Rect(self._location[0] - self.SIZE / 2,
                                 self._location[1] - self.SIZE / 2,
                                 self.SIZE,
                                 self.SIZE
                                 )
        self.hilited = False

    def _make_image(self, filename, size):
        """ Loads a graphic file and returns a ready to display image object of
        the indicated size.

        Parameters:
            filename:
                the graphic file name, which must be stored in the res/ dubdir
            size:
                the resulting image size (width)

        Returns:
            a PyGame image object
        """
        raw_img = pygame.image.load(utils.make_resource_path(filename)).convert_alpha()
        raw_size = raw_img.get_size()
        scale = size / raw_size[0]
        return pygame.transform.smoothscale(
            raw_img,
            tuple(int(d * scale) for d in raw_size)
        )

    @property
    def location(self):
        """ Object center position on the display."""
        return self._location

    @property
    def heading(self):
        """ Current heading of the beacon dish."""
        return self._heading

    @heading.setter
    def heading(self, hdg):
        if hdg != None:
            self._heading = min(max(hdg, self._scan_range[0]), self._scan_range[1])
        else:
            self._heading = None

    @property
    def heading_min(self):
        """ Lower bound of the scan range."""
        return self._scan_range[0]

    @property
    def heading_max(self):
        """ Upper bound of the scan range."""
        return self._scan_range[1]

    @property
    def target_heading(self):
        return self._target_heading

    @target_heading.setter
    def target_heading(self, angle):
        self._new_echo = True
        self._target_heading = angle
        self._target_heading_when = time.time()

    def draw(self, surface):
        """ Draws the beacon and its decorations (mouse interaction feedback, ray).

        The ray display is made remanent, by fading away during the delay indicated
        by RAY_MAX_AGE (in seconds).

        If the hilited attribute is set, the hiliting image is surimposed at the end
        of the drawing.
        """
        now = time.time()

        if self._target_heading:
            target_heading_age = now - self._target_heading_when
            if target_heading_age > self.TARGET_HEADING_MAX_AGE:
                self._target_heading = None

        if self._new_echo:
            # got a target echo => activates the ray display
            self._ray_when = time.time()
            self._log.debug('turn ray on')
            self._new_echo = False

        x0, y0 = self._location

        # ray drawing
        if self._ray_when != None and self._target_heading != None:
            a = math.radians(self._target_heading - 90)
            cos_a, sin_a = math.cos(a), math.sin(a)
            start_dist = 50
            ray_x0, ray_y0 = x0 + start_dist * cos_a, y0 - start_dist * sin_a
            ray_x1, ray_y1 = x0 + self._ray_length * cos_a, y0 - self._ray_length * sin_a

            ray_age = now - self._ray_when

            lum = max(1. - ray_age / self.RAY_MAX_AGE, 0)
            color = tuple(int(c * lum) for c in self._ray_color)
            pygame.draw.aaline(surface, color, (ray_x0, ray_y0), (ray_x1, ray_y1))

            color = tuple(int(c * lum) for c in self._angle_label_color)
            r = pygame.Rect(x0 - 200, y0 - 200, 400, 400)
            arc_start = min(a, math.radians(-90))
            arc_end = max(a, math.radians(-90))
            pygame.draw.arc(surface, color, r, arc_start, arc_end, 3)

            # angle origin axis
            pygame.draw.line(surface, color, (x0, y0 + 50), (x0, y0 + 300))

            a = math.radians(self._target_heading / 2. - 90)
            x = x0 + 150. * math.cos(a) - self._angle_label.get_width() / 2
            y = y0 - 150. * math.sin(a) - self._angle_label.get_height() / 2
            surface.blit(self._angle_label, (x, y))

            if ray_age > self.RAY_MAX_AGE:
                self._ray_when = None
                self._log.debug('turn ray off')

        # beacon parts drawing
        surface.blit(self._img_base, (x0 - self.SIZE / 2, y0 - self.SIZE / 2))
        angle = self._heading
        surf = pygame.transform.rotozoom(self._img_dish, angle, 1)
        w, h = surf.get_size()
        surface.blit(surf, (x0 - w / 2, y0 - h / 2))

        # hilite drawing
        if self.hilited:
            surface.blit(self._img_hilite, (x0 - self.SIZE / 2, y0 - self.SIZE / 2))


    def collidepoint(self, pos):
        """ Returns true if the given position (x, y) is inside the bounding rect."""
        return self._rect.collidepoint(pos)


class TextWindow(DisplayObject):
    bkgnd_file = None

    def __init__(self, geom, color=pygame.Color('green')):
        """ Constructor.

        Parameters:
            geom:
                the bounding rectangle of the window
        """
        self._font = pygame.font.SysFont('Courier', 14, bold=False)
        self._lineheight = self._font.get_linesize()

        self._topleft = utils.Point(geom.topleft)
        self._childrect = pygame.Rect(0, 0, geom.w, geom.h)
        self._text_color = color

        if self.bkgnd_file:
            self._bkgnd = pygame.image.load(
                utils.make_resource_path(self.bkgnd_file)
            ).convert_alpha()
            self._bkgnd.set_clip(self._childrect)
        else:
            self._bkgnd = pygame.Surface( #pylint: disable=E1121,E1123
                geom.size,
                flags=pygame.SRCALPHA
            )
            self._bkgnd.fill((40, 40, 40, 220))

    def _write(self, text, pos, surface):
        surf = self._font.render(
            text,
            True,
            self._text_color
        )
        surface.blit(surf, dest=pos.xy)

    def draw(self, surface):
        surface.blit(
            source=self._bkgnd,
            dest=self._topleft.xy,
            area=self._childrect
        )


class Hud(TextWindow):
    """ Head Up Display providing information such as the FPS, the beacon angles,
    the target position,..."""

    bkgnd_file = 'scanlines.png'

    def __init__(self, geom):
        """ Constructor.

        Parameters:
            geom:
                the bounding rectangle of the HUD
        """
        super(Hud, self).__init__(geom)

        self.alpha = None
        self.beta = None
        self.target_location = None

    def draw(self, surface):
        super(Hud, self).draw(surface)

        txt_pos = utils.Point(self._topleft).move(40, 10)

        s_alpha = '%4.1f' % self.alpha if self.alpha != None else '....'
        s_beta = '%4.1f' % self.beta if self.beta != None else '....'
        s_x = '%4d' % self.target_location[0] if self.target_location else '....'
        s_y = '%4d' % self.target_location[1] if self.target_location else '....'
        self._write(
            'alpha : %s / beta : %s / x : %s / y : %s' % (s_alpha, s_beta, s_x, s_y),
            txt_pos,
            surface
        )


class StatusLine(TextWindow):
    def __init__(self, geom):
        super(StatusLine, self).__init__(geom, color=pygame.Color(127, 127, 127, 255))
        self.controller = None
        self.fps = 0

    def draw(self, surface):
        super(StatusLine, self).draw(surface)
        txt_pos = utils.Point(self._topleft).move(10, 0)
        s = '%s (%s) / FPS: %d' % (
            self.controller[0], self.controller[2][0], self.fps
        )
        self._write(s, txt_pos, surface)


class Logo(DisplayObject):
    """ POBOT logo display object."""

    def __init__(self, display_size):
        """ Constructor.

        Parameters:
            display_size:
                the size of the display size, for positionning the logo in
                one of its angles.
        """
        raw_logo = pygame.image.load(
            utils.make_resource_path('pobot-logo.png')
        ).convert_alpha()
        raw_size = raw_logo.get_size()
        scale = 120. / raw_size[0]
        self._img = pygame.transform.smoothscale(
            raw_logo,
            tuple(int(d * scale) for d in raw_size)
        )
        self._logo_pos = (
            display_size[0] - self._img.get_size()[0],
            display_size[1] - self._img.get_size()[1]
        )

    def draw(self, surface):
        surface.blit(self._img, self._logo_pos)


class Target(DisplayObject):
    """ Detected target display objet."""
    WIDTH = 100
    FADE_OUT_DELAY = 1.

    def __init__(self):
        raw_img = pygame.image.load(
            utils.make_resource_path('cartoon_robot.png')
        ).convert_alpha()
        raw_size = raw_img.get_size()
        scale = float(self.WIDTH) / raw_size[0]
        self._img = pygame.transform.smoothscale(
            raw_img,
            tuple(int(d * scale) for d in raw_size)
        )
        self._size = self._img.get_size()
        self._location = (0, 0)
        self._visible = False
        self._visible_since = None

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, loc):
        self._location = loc

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, visible):
        self._visible = visible

    def draw(self, surface):
        if self._visible:
            self._visible_since = time.time()
            alpha = 255
        elif self._visible_since != None:
            alpha = round(
                255 * min(1, (1 - (time.time() - self._visible_since) / self.FADE_OUT_DELAY))
            )
        else:
            alpha = 0

        if alpha:
            origin = (
                self.location[0] - self._size[0] / 2.,
                self.location[1] - self._size[1] / 2.
            )
            surf = pygame.surface.Surface(self._img.get_size()).convert()
            surf.blit(surface, (-origin[0], -origin[1]))
            surf.blit(self._img, (0, 0))
            surf.set_alpha(alpha)
            surface.blit(surf, origin)


class Help(TextWindow):
    text = """
Beacon GUI help
---------------

S ........ starts beacon scanning
s ........ stops beacon scanning
L ........ activates laser
l ........ de-activates laser

Esc ...... closes this help
Alt-F4 ... exits application
"""
    def __init__(self, geom):
        """ Constructor.

        Parameters:
            geom:
                the bounding rectangle of the HUD
        """
        super(Help, self).__init__(geom)

        self._lines = self.text.strip().split('\n')

    def draw(self, surface):
        super(Help, self).draw(surface)

        txt_pos = utils.Point(self._topleft)
        txt_pos.move(10, 10)

        for line in self._lines:
            self._write(line, txt_pos, surface)
            txt_pos.move(0, self._lineheight)

