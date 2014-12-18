# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import time


# Register addresses.
MPR121_I2CADDR_DEFAULT = 0x5A
MPR121_TOUCHSTATUS_L   = 0x00
MPR121_TOUCHSTATUS_H   = 0x01
MPR121_FILTDATA_0L     = 0x04
MPR121_FILTDATA_0H     = 0x05
MPR121_BASELINE_0      = 0x1E
MPR121_MHDR            = 0x2B
MPR121_NHDR            = 0x2C
MPR121_NCLR            = 0x2D
MPR121_FDLR            = 0x2E
MPR121_MHDF            = 0x2F
MPR121_NHDF            = 0x30
MPR121_NCLF            = 0x31
MPR121_FDLF            = 0x32
MPR121_NHDT            = 0x33
MPR121_NCLT            = 0x34
MPR121_FDLT            = 0x35
MPR121_TOUCHTH_0       = 0x41
MPR121_RELEASETH_0     = 0x42
MPR121_DEBOUNCE        = 0x5B
MPR121_CONFIG1         = 0x5C
MPR121_CONFIG2         = 0x5D
MPR121_CHARGECURR_0    = 0x5F
MPR121_CHARGETIME_1    = 0x6C
MPR121_ECR             = 0x5E
MPR121_AUTOCONFIG0     = 0x7B
MPR121_AUTOCONFIG1     = 0x7C
MPR121_UPLIMIT         = 0x7D
MPR121_LOWLIMIT        = 0x7E
MPR121_TARGETLIMIT     = 0x7F
MPR121_GPIODIR         = 0x76
MPR121_GPIOEN          = 0x77
MPR121_GPIOSET         = 0x78
MPR121_GPIOCLR         = 0x79
MPR121_GPIOTOGGLE      = 0x7A
MPR121_SOFTRESET       = 0x80


class MPR121(object):
    """Representation of a MPR121 capacitive touch sensor."""

    def __init__(self):
        """Create an instance of the MPR121 device."""
        # Nothing to do here since there is very little state in the class.
        pass

    def begin(self, address=MPR121_I2CADDR_DEFAULT, i2c=None, **kwargs):
        """Initialize communication with the MPR121. 

        Can specify a custom I2C address for the device using the address 
        parameter (defaults to 0x5A). Optional i2c parameter allows specifying a 
        custom I2C bus source (defaults to platform's I2C bus).

        Returns True if communication with the MPR121 was established, otherwise
        returns False.
        """
        # Assume we're using platform's default I2C bus if none is specified.
        if i2c is None:
            import Adafruit_GPIO.I2C as I2C
            i2c = I2C
        # Save a reference to the I2C device instance for later communication.
        self._device = i2c.get_i2c_device(address, **kwargs)
        # Soft reset of device.
        self._device.write8(MPR121_SOFTRESET, 0x63)
        time.sleep(0.001) # This 1ms delay here probably isn't necessary but can't hurt.
        # Set electrode configuration to default values.
        self._device.write8(MPR121_ECR, 0x00)
        # Check CDT, SFI, ESI configuration is at default values.
        # NOTE: This is commented out for now because it _requires_ a repeated 
        # I2C start condition to read the register and the Pi doesn't easily
        # support that reading mode.  There's more info in this thread (and a
        # workaround to enable the mode), but for now this check isn't critical.
        #   http://www.raspberrypi.org/forums/viewtopic.php?f=44&t=15840
        #c = self._device.readU8(MPR121_CONFIG2)
        #if c != 0x24:
        #   return False
        # Set threshold for touch and release to default values.
        self.set_thresholds(12, 6)
        # Configure baseline filtering control registers.
        self._device.write8(MPR121_MHDR, 0x01)
        self._device.write8(MPR121_NHDR, 0x01)
        self._device.write8(MPR121_NCLR, 0x0E)
        self._device.write8(MPR121_FDLR, 0x00)
        self._device.write8(MPR121_MHDF, 0x01)
        self._device.write8(MPR121_NHDF, 0x05)
        self._device.write8(MPR121_NCLF, 0x01)
        self._device.write8(MPR121_FDLF, 0x00)
        self._device.write8(MPR121_NHDT, 0x00)
        self._device.write8(MPR121_NCLT, 0x00)
        self._device.write8(MPR121_FDLT, 0x00)
        # Set other configuration registers.
        self._device.write8(MPR121_DEBOUNCE, 0)
        self._device.write8(MPR121_CONFIG1, 0x10) # default, 16uA charge current
        self._device.write8(MPR121_CONFIG2, 0x20) # 0.5uS encoding, 1ms period
        # Enable all electrodes.
        self._device.write8(MPR121_ECR, 0x8F) # start with first 5 bits of baseline tracking
        # All done, everything succeeded!
        return True

    def set_thresholds(self, touch, release):
        """Set the touch and release threshold for all inputs to the provided
        values.  Both touch and release should be a value between 0 to 255
        (inclusive).
        """
        assert touch >= 0 and touch <= 255, 'touch must be between 0-255 (inclusive)'
        assert release >= 0 and release <= 255, 'release must be between 0-255 (inclusive)'
        # Set the touch and release register value for all the inputs.
        for i in range(12):
            self._device.write8(MPR121_TOUCHTH_0 + 2*i, touch)
            self._device.write8(MPR121_RELEASETH_0 + 2*i, release)

    def filtered_data(self, pin):
        """Return filtered data register value for the provided pin (0-11).
        Useful for debugging.
        """
        assert pin >= 0 and pin < 12, 'pin must be between 0-11 (inclusive)'
        return self._device.readU16LE(MPR121_FILTDATA_0L + pin*2)

    def baseline_data(self, pin):
        """Return baseline data register value for the provided pin (0-11).
        Useful for debugging.
        """
        assert pin >= 0 and pin < 12, 'pin must be between 0-11 (inclusive)'
        bl = self._device.readU8(MPR121_BASELINE_0 + pin)
        return bl << 2

    def touched(self):
        """Return touch state of all pins as a 12-bit value where each bit 
        represents a pin, with a value of 1 being touched and 0 not being touched.
        """
        t = self._device.readU16LE(MPR121_TOUCHSTATUS_L)
        return t & 0x0FFF

    def is_touched(self, pin):
        """Return True if the specified pin is being touched, otherwise returns
        False.
        """
        assert pin >= 0 and pin < 12, 'pin must be between 0-11 (inclusive)'
        t = self.touched()
        return (t & (1 << pin)) > 0