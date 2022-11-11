import unittest

from dineniso5167 import core


class TestCore(unittest.TestCase):

    def test_beta(self):
        with self.assertWarns(Warning):
            core.compute_beta(1, 12, 'mm')
        with self.assertRaises(ValueError):
            core.compute_beta(20, 10, 'mm')
        with self.assertWarns(Warning):
            core.compute_beta(13, 20, 'mm')
        self.assertEqual(1/12, core.compute_beta(1, 12, 'mm'))
        self.assertEqual(13/20, core.compute_beta(13, 20, 'mm'))
        self.assertEqual(60/100, core.compute_beta(60, 100, 'mm'))

    def test_density(self):
        self.assertEqual(round(core.compute_density(101325, 15.+core.T0_Kelvin, 0), 4), 1.225)

    def test_vfr(self):
        vfr_value, vfr_value_min, vfr_value_max, dp_loss = core.compute_volume_flow_rate(dp=100,
                                                                                         d=60.,
                                                                                         D=120.,
                                                                                         length_unit='mm',
                                                                                         p1=101325,
                                                                                         T=22.,
                                                                                         phi=0.4,
                                                                                         kappa=1.4,
                                                                                         Cguess=0.6183,
                                                                                         verbose=True)
        self.assertAlmostEqual(vfr_value, 0.02302704683261634)
