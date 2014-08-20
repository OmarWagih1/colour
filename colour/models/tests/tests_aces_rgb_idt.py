#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Defines unit tests for :mod:`colour.models.aces_rgb_idt` module.
"""

from __future__ import division, unicode_literals

import sys
import numpy as np

if sys.version_info[:2] <= (2, 6):
    import unittest2 as unittest
else:
    import unittest

from colour.characterization import COLOURCHECKERS_SPDS
from colour.colorimetry import SpectralPowerDistribution
from colour.models import ACES_RICD, spectral_to_aces_relative_exposure_values

__author__ = 'Colour Developers'
__copyright__ = 'Copyright (C) 2013 - 2014 - Colour Developers'
__license__ = 'New BSD License - http://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Colour Developers'
__email__ = 'colour-science@googlegroups.com'
__status__ = 'Production'

__all__ = ['TestXYZ_to_Lab',
           'TestLab_to_XYZ',
           'TestLab_to_LCHab',
           'TestLCHab_to_Lab']


class TestSpectralToAcesRelativeExposureValues(unittest.TestCase):
    """
    Defines :func:`colour.models.aces_rgb_idt.spectral_to_aces_relative_exposure_values`
    definition unit tests methods.
    """

    def test_spectral_to_aces_relative_exposure_values(self):
        """
        Tests :func:`colour.models.aces_rgb_idt.spectral_to_aces_relative_exposure_values`
        definition.
        """

        wavelengths = ACES_RICD.wavelengths
        grey_reflector = SpectralPowerDistribution(
            '18%',
            dict(zip(wavelengths, [0.18] * len(wavelengths))))
        np.testing.assert_almost_equal(
            spectral_to_aces_relative_exposure_values(grey_reflector),
            np.array([0.18, 0.18, 0.18]))

        perfect_reflector = SpectralPowerDistribution(
            '100%',
            dict(zip(wavelengths, [1] * len(wavelengths))))
        np.testing.assert_almost_equal(
            spectral_to_aces_relative_exposure_values(perfect_reflector),
            np.array([1., 1., 1.]))

        dark_skin = (
            COLOURCHECKERS_SPDS.get('ColorChecker N Ohta').get('dark skin'))
        np.testing.assert_almost_equal(
            spectral_to_aces_relative_exposure_values(dark_skin),
            np.array([0.11713776, 0.08461404, 0.05545923]))


if __name__ == '__main__':
    unittest.main()