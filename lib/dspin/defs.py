#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" dSpin (aka STMicroElectronics L6470) package.

Symbolic constants definitions.

Reference documentation available at:
    http://www.st.com/internet/analog/product/248592.jsp
Have also a llok at this article:
    http://www.pobot.org/Driver-evolue-pour-moteur-pas-a.html
"""

__author__ = "Eric Pascual"
__email__ = "eric@pobot.org"
__copyright__ = "Copyright 2013, POBOT"
__version__ = "1.0"
__date__ = "July. 2013"
__status__ = "Development"
__license__ = "LGPL"

#
# dSpin registers
#

dSPIN_REG_ABS_POS       = 0x01
dSPIN_REG_EL_POS        = 0x02
dSPIN_REG_MARK          = 0x03
dSPIN_REG_SPEED         = 0x04
dSPIN_REG_ACC           = 0x05
dSPIN_REG_DEC           = 0x06
dSPIN_REG_MAX_SPEED     = 0x07
dSPIN_REG_MIN_SPEED     = 0x08
dSPIN_REG_KVAL_HOLD     = 0x09
dSPIN_REG_KVAL_RUN      = 0x0A
dSPIN_REG_KVAL_ACC      = 0x0B
dSPIN_REG_KVAL_DEC      = 0x0C
dSPIN_REG_INT_SPD       = 0x0D
dSPIN_REG_ST_SLP        = 0x0E
dSPIN_REG_FN_SLP_ACC    = 0x0F
dSPIN_REG_FN_SLP_DEC    = 0x10
dSPIN_REG_K_THERM       = 0x11
dSPIN_REG_ADC_OUT       = 0x12
dSPIN_REG_OCD_TH        = 0x13
dSPIN_REG_STALL_TH      = 0x14
dSPIN_REG_FS_SPD        = 0x15
dSPIN_REG_STEP_MODE     = 0x16
dSPIN_REG_ALARM_EN      = 0x17
dSPIN_REG_CONFIG        = 0x18
dSPIN_REG_STATUS        = 0x19

#
# dSpin commands
#
# Identifiers names are built by prepending "dSPIN_CMD_" to the register name,
# as it appears in the datasheet.
#

dSPIN_CMD_NOP           = 0x00
dSPIN_CMD_SET_PARAM     = 0x00
dSPIN_CMD_GET_PARAM     = 0x20
dSPIN_CMD_RUN           = 0x50
dSPIN_CMD_STEP_CLOCK    = 0x58
dSPIN_CMD_MOVE          = 0x40
dSPIN_CMD_GOTO          = 0x60
dSPIN_CMD_GOTO_DIR      = 0x68
dSPIN_CMD_GO_UNTIL      = 0x82
dSPIN_CMD_RELEASE_SW    = 0x92
dSPIN_CMD_GO_HOME       = 0x70
dSPIN_CMD_GO_MARK       = 0x78
dSPIN_CMD_RESET_POS     = 0xD8
dSPIN_CMD_RESET_DEVICE  = 0xC0
dSPIN_CMD_SOFT_STOP     = 0xB0
dSPIN_CMD_HARD_STOP     = 0xB8
dSPIN_CMD_SOFT_HIZ      = 0xA0
dSPIN_CMD_HARD_HIZ      = 0xA8
dSPIN_CMD_GET_STATUS    = 0xD0

#
# STEP_MODE register
#

dSPIN_STEP_MODE_SYNC_EN     = 0x80  # SYNC_EN field mask
dSPIN_STEP_MODE_SYNC_SEL    = 0x70  # SYNC_SEL field mask
dSPIN_STEP_MODE_WRITE       = 0x08  # WRITE field mask
dSPIN_STEP_MODE_STEP_SEL    = 0x07  # STEP_SEL field mask

#
# Step modes.
#

dSPIN_STEP_SEL_1        = 0x00
dSPIN_STEP_SEL_1_2      = 0x01
dSPIN_STEP_SEL_1_4      = 0x02
dSPIN_STEP_SEL_1_8      = 0x03
dSPIN_STEP_SEL_1_16     = 0x04
dSPIN_STEP_SEL_1_32     = 0x05
dSPIN_STEP_SEL_1_64     = 0x06
dSPIN_STEP_SEL_1_128    = 0x07

#
# Sync modes.
#

dSPIN_SYNC_SEL_1_2      = 0x00
dSPIN_SYNC_SEL_1        = 0x10
dSPIN_SYNC_SEL_2        = 0x20
dSPIN_SYNC_SEL_4        = 0x30
dSPIN_SYNC_SEL_8        = 0x40
dSPIN_SYNC_SEL_16       = 0x50
dSPIN_SYNC_SEL_32       = 0x60
dSPIN_SYNC_SEL_64       = 0x70

#
# Sync enabling.
#

dSPIN_SYNC_EN           = 0x80
dSPIN_SYNC_DIS          = 0x00

#
# ALARM_EN register flags.
#

dSPIN_ALARM_EN_OVERCURRENT          = 0x0
dSPIN_ALARM_EN_THERMAL_SHUTDOWN     = 0x0
dSPIN_ALARM_EN_THERMAL_WARNING      = 0x0
dSPIN_ALARM_EN_UNDER_VOLTAGE        = 0x0
dSPIN_ALARM_EN_STALL_DET_A          = 0x1
dSPIN_ALARM_EN_STALL_DET_B          = 0x2
dSPIN_ALARM_EN_SW_TURN_ON           = 0x4
dSPIN_ALARM_EN_WRONG_NPERF_CMD      = 0x80

#
# CONFIG register
#

dSPIN_CONFIG_OSC_SEL                 = 0x000F   # OSC_SEL field mask
dSPIN_CONFIG_SW_MODE                 = 0x0010   # SW_MODE field mask
dSPIN_CONFIG_EN_VSCOMP               = 0x0020   # EN_VSCOMP field mask
dSPIN_CONFIG_OC_SD                   = 0x0080   # OC_SD field mask
dSPIN_CONFIG_POW_SR                  = 0x0300   # POW_SR field mask
dSPIN_CONFIG_F_PWM_DEC               = 0x1C00   # F_PWM_DEC field mask
dSPIN_CONFIG_F_PWM_INT               = 0xE000   # F_PWM_INT field mask

#
# Bit masks used by the register descriptors
#

MASK_4      = 0x00000F
MASK_5      = 0x00001F
MASK_7      = 0x00007F
MASK_8      = 0x0000FF
MASK_9      = 0x0001FF
MASK_10     = 0x0003FF
MASK_12     = 0x000FFF
MASK_13     = 0x001FFF
MASK_14     = 0x003FFF
MASK_16     = 0x00FFFF
MASK_20     = 0x0FFFFF
MASK_22     = 0x3FFFFF

#
# dSPIN register descritors table
#
# The table is indexed by the register number, and contains tuples
# providing :
#   - the register size (in bytes)
#   - the data value used bits as a mask
#

dSPIN_REG_DESCR = [
        ( 0, 0 ),           # reg 0 does not exist
        ( 3, MASK_22 ),     # dSPIN_REG_ABS_POS
        ( 2, MASK_9 ),      # dSPIN_REG_EL_POS
        ( 3, MASK_22 ),     # dSPIN_REG_MARK
        ( 3, MASK_20 ),     # dSPIN_REG_SPEED
        ( 2, MASK_12 ),     # dSPIN_REG_ACC
        ( 2, MASK_12 ),     # dSPIN_REG_DEC
        ( 2, MASK_10 ),     # dSPIN_REG_MAX_SPEED
        ( 2, MASK_13 ),     # dSPIN_REG_MIN_SPEED
        ( 1, MASK_8 ),      # dSPIN_REG_KVAL_HOLD
        ( 1, MASK_8 ),      # dSPIN_REG_KVAL_RUN
        ( 1, MASK_8 ),      # dSPIN_REG_KVAL_ACC
        ( 1, MASK_8 ),      # dSPIN_REG_KVAL_DEC
        ( 2, MASK_14 ),     # dSPIN_REG_INT_SPD
        ( 1, MASK_8 ),      # dSPIN_REG_ST_SLP
        ( 1, MASK_8 ),      # dSPIN_REG_FN_SLP_ACC
        ( 1, MASK_8 ),      # dSPIN_REG_FN_SLP_DEC
        ( 1, MASK_4 ),      # dSPIN_REG_K_THERM
        ( 1, MASK_5 ),      # dSPIN_REG_ADC_OUT
        ( 1, MASK_4 ),      # dSPIN_REG_OCD_TH
        ( 1, MASK_7 ),      # dSPIN_REG_STALL_TH
        ( 2, MASK_10 ),     # dSPIN_REG_FS_SPD
        ( 1, MASK_8 ),      # dSPIN_REG_STEP_MODE
        ( 1, MASK_8 ),      # dSPIN_REG_ALARM_EN
        ( 2, MASK_16 ),     # dSPIN_REG_CONFIG
        ( 2, MASK_16 )      # dSPIN_REG_STATUS
]

#
# Oscillator selectors
#

dSPIN_OSC_SEL_INT_16MHZ = 0x0000                # Internal 16MHz, no output
dSPIN_OSC_SEL_INT_16MHZ_OSCOUT_2MHZ = 0x0008    # Default; internal 16MHz 2MHz output
dSPIN_OSC_SEL_INT_16MHZ_OSCOUT_4MHZ = 0x0009    # Internal 16MHz 4MHz output
dSPIN_OSC_SEL_INT_16MHZ_OSCOUT_8MHZ = 0x000A    # Internal 16MHz 8MHz output
dSPIN_OSC_SEL_INT_16MHZ_OSCOUT_16MHZ = 0x000B   # Internal 16MHz 16MHz output
dSPIN_OSC_SEL_EXT_8MHZ_XTAL_DRIVE = 0x0004      # External 8MHz crystal
dSPIN_OSC_SEL_EXT_16MHZ_XTAL_DRIVE = 0x0005     # External 16MHz crystal
dSPIN_OSC_SEL_EXT_24MHZ_XTAL_DRIVE = 0x0006     # External 24MHz crystal
dSPIN_OSC_SEL_EXT_32MHZ_XTAL_DRIVE = 0x0007     # External 32MHz crystal
dSPIN_OSC_SEL_EXT_8MHZ_OSCOUT_INVERT = 0x000C   # External 8MHz crystal output inverted
dSPIN_OSC_SEL_EXT_16MHZ_OSCOUT_INVERT = 0x000D  # External 16MHz crystal output inverted
dSPIN_OSC_SEL_EXT_24MHZ_OSCOUT_INVERT = 0x000E  # External 24MHz crystal output inverted
dSPIN_OSC_SEL_EXT_32MHZ_OSCOUT_INVERT = 0x000F  # External 32MHz crystal output inverted

#
# Switch signal usage
#

dSPIN_SW_MODE_HARD_STOP = 0x0000    # Default; hard stop motor on switch.
dSPIN_SW_MODE_USER = 0x0010         # Tie to the GoUntil and ReleaseSW

#
# Motor voltage compensation mode
#

dSPIN_VS_COMP_DISABLE = 0x0000      # Disable motor voltage compensation.
dSPIN_VS_COMP_ENABLE = 0x0020       # Enable motor voltage compensation.

#
# Over-current shutdown settings
#

dSPIN_OC_SD_DISABLE = 0x0000        # Bridges do NOT shutdown on OC detect
dSPIN_OC_SD_ENABLE = 0x0080         # Bridges shutdown on OC detect

#
# Power slew-rate settings
#

dSPIN_POW_SR_180V_us = 0x0000       # 180V/us
dSPIN_POW_SR_290V_us = 0x0200       # 290V/us
dSPIN_POW_SR_530V_us = 0x0300       # 530V/us

#
# PWM clock divider
#

dSPIN_PWM_DIV_1 = (0x00) << 13
dSPIN_PWM_DIV_2 = (0x01) << 13
dSPIN_PWM_DIV_3 = (0x02) << 13
dSPIN_PWM_DIV_4 = (0x03) << 13
dSPIN_PWM_DIV_5 = (0x04) << 13
dSPIN_PWM_DIV_6 = (0x05) << 13
dSPIN_PWM_DIV_7 = (0x06) << 13

#
# PWM clock multiplier
#

dSPIN_PWM_MUL_0_625 = (0x00) << 10
dSPIN_PWM_MUL_0_75 = (0x01) << 10
dSPIN_PWM_MUL_0_875 = (0x02) << 10
dSPIN_PWM_MUL_1 = (0x03) << 10
dSPIN_PWM_MUL_1_25 = (0x04) << 10
dSPIN_PWM_MUL_1_5 = (0x05) << 10
dSPIN_PWM_MUL_1_75 = (0x06) << 10
dSPIN_PWM_MUL_2 = (0x07) << 10

#
# STATUS register masks
#

dSPIN_STATUS_HIZ                     = 0x0001 # high when bridges are in HiZ mode
dSPIN_STATUS_BUSY                    = 0x0002 # mirrors BUSY pin
dSPIN_STATUS_SW_F                    = 0x0004 # low when switch open, high when closed
dSPIN_STATUS_SW_EVN                  = 0x0008 # active high, set on switch falling edge,
dSPIN_STATUS_DIR                     = 0x0010 # Indicates current motor direction.
dSPIN_STATUS_MOT_STATUS              = 0x0060 # Motor status
dSPIN_STATUS_NOTPERF_CMD             = 0x0080 # Last command not performed.
dSPIN_STATUS_WRONG_CMD               = 0x0100 # Last command not valid.
dSPIN_STATUS_UVLO                    = 0x0200 # Undervoltage lockout is active
dSPIN_STATUS_TH_WRN                  = 0x0400 # Thermal warning
dSPIN_STATUS_TH_SD                   = 0x0800 # Thermal shutdown
dSPIN_STATUS_OCD                     = 0x1000 # Overcurrent detected
dSPIN_STATUS_STEP_LOSS_A             = 0x2000 # Stall detected on A bridge
dSPIN_STATUS_STEP_LOSS_B             = 0x4000 # Stall detected on B bridge
dSPIN_STATUS_SCK_MOD                 = 0x8000 # Step clock mode is active

#
# Motor status values
#

dSPIN_MOT_STATUS_STOPPED = 0                 # Motor stopped
dSPIN_MOT_STATUS_ACCELERATION = 0x01 << 5    # Motor accelerating
dSPIN_MOT_STATUS_DECELERATION = 0x02 << 5    # Motor decelerating
dSPIN_MOT_STATUS_CONST_SPD = 0x03 << 5       # Motor at constant speed

#
# Motor directions
#

dSPIN_DIR_REV = 0x00
dSPIN_DIR_FWD = 0x01

#
# Action options
#

dSPIN_ACTION_RESET = 0x00
dSPIN_ACTION_COPY = 0x01

#
# Factory reset configuration register value
#

dSPIN_FACT_RESET_CONFIG = 0x2E88


