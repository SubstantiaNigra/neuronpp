import os
import unittest
import numpy as np
from neuron import h
from neuronpp.core.cells.spine_cell import SpineCell
from neuronpp.core.cells.utils import establish_electric_properties
from neuronpp.core.cells.utils import get_spine_number

class TestParentSectionElectric(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cell =  SpineCell(name="cell")
        cls.soma = cell.add_sec("soma", g_leak=1/30000, E_rest=-76,
                                ra=40, cm=1.1, add_leak=True)
        cls.e_leak1, cls.g_pas1, cls.ra1, cls.cm1 = establish_electric_properties(cls.soma,
                                                                            None, None,
                                                                            None, None)
        
        cls.e_leak2, cls.g_pas2, cls.ra2, cls.cm2 = establish_electric_properties(cls.soma,
                                                                              -79, 1/20000,
                                                                              50, 1.2)

    def test_e_leak_soma(self):
        self.assertEqual(self.soma.hoc.e_pas, self.e_leak1)

    def test_g_pas_soma(self):
        out = np.isclose(self.soma.hoc.g_pas, self.g_pas1)
        self.assertTrue(out)

    def test_ra_soma(self):
        self.assertEqual(self.soma.hoc.Ra, self.ra1)

    def test_cm_soma(self):
        self.assertEqual(self.soma.hoc.cm, self.cm1)

    def test_e_leak(self):
        self.assertEqual(self.e_leak2, -79)

    def test_g_pas(self):
        out = np.isclose(self.g_pas2, 1/20000)
        self.assertTrue(out)

    def test_ra(self):
        self.assertEqual(self.ra2, 50)

    def test_cm(self):
        self.assertEqual(self.cm2, 1.2)

class TestGetSpineNumber(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cell = SpineCell(name="cell")
        cls.soma = cell.add_sec("soma")

    def test_length_density(self):
        spine_density = 0.1
        out = get_spine_number(self.soma, spine_density, False)
        self.assertEqual(out, 10)

    def test_area_density(self):
        spine_density = 0.01
        out = get_spine_number(self.soma, spine_density, True)
        expected = int(np.ceil(np.pi*spine_density*self.soma.hoc.L*self.soma.hoc.diam))
        self.assertEqual(out, expected)

    def test_very_small(self):
        spine_density = 0.0001
        out = get_spine_number(self.soma, spine_density, False)
        self.assertTrue(out in [0, 1])
    
