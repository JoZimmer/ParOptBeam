import unittest
import mock
import numpy as np
from scipy import linalg
from source.model.structure_model import StraightBeam

class test_structure_model_decompose_and_qunatify_eigenmodes(unittest.TestCase):
    
    def create_mock_self_for_contribution (self):
        mock_self = mock.MagicMock()
        mock_self.eig_freqs_sorted_indices = np.array([0])
        mock_self.dofs_to_keep = np.array([0])
        mock_self.domain_size = '3D'
        mock_self.eigen_modes_raw = np.array([
        [-3.53420556e-19], [1.63043899e-19],  [8.50278725e-19],  [-4.77395127e-19],
        [-9.19617850e-19], [-2.30959794e-33], [-4.39066387e-19], [2.25363084e-19],
        [-5.55596213e-20], [9.83695305e-20],  [1.73710162e-34],  [3.33840178e-20],
        [-3.83894809e-20], [1.77468855e-35],  [5.77372089e-03],  [-1.25517271e-20],
        [-1.38232703e-02], [-9.17897402e-03]])
        mock_self.charact_length = 0.3
        mock_self.n_elements = 3
        mock_self.parameters['m'] = [2616.6666666666665, 5233.333333333333, 5233.333333333334, 2616.6666666666674]
        mock_self.parameters['lz'] = [0.4, 0.4, 0.4, 0.4]
        mock_self.parameters['ly'] = [0.2, 0.2, 0.2, 0.2]
        mock_self.contribution_matlab_solution = np.array([
            1.69482512506842e-19,	8.34473782500097e-20,
        	0.00173211626700000,	4.87586113078838e-19,
            0.0138232703000000,	0.00917897402000000])
        return mock_self

    def create_mock_self_for_modal_mass (self):
        mock_self = mock.MagicMock()
        mock_self.eig_freqs_sorted_indices = np.array([0])
        mock_self.dofs_to_keep = np.array([0])
        mock_self.domain_size = '3D'
        mock_self.eigen_modes_raw = np.ones([18,1])/(np.sqrt(3))
        # --> norm(decomposed_mode) == 1
        mock_self.charact_length = 1
        mock_self.n_elements = 3
        mock_self.contribution_matlab_solution = np.array([
            1.69482512506842e-19,	8.34473782500097e-20,
        	0.00173211626700000,	4.87586113078838e-19,
            0.0138232703000000,	0.00917897402000000])
        return mock_self

    @mock.patch('builtins.zip')
    @mock.patch('source.model.structure_model.StraightBeam.eigenvalue_solve')
    def test_contribution_0_a (self,mock_eigenvalue_solve,mock_zip):
        mock_self = self.create_mock_self_for_contribution()
        idx = 0
        label = 'a'
        mock_zip.return_value = [[idx,label]]
        StraightBeam.decompose_and_quantify_eigenmodes(mock_self) 
        self.assertEqual(mock_self.decomposed_eigenmodes['rel_contribution'][0],{label: mock_self.charact_length * linalg.norm(mock_self.eigen_modes_raw[idx:(13+idx):6][:,0])})
        self.assertIsNone(np.testing.assert_allclose(mock_self.decomposed_eigenmodes['rel_contribution'][0][label], mock_self.contribution_matlab_solution[idx]))

    @mock.patch('builtins.zip')
    @mock.patch('source.model.structure_model.StraightBeam.eigenvalue_solve')
    def test_contribution_1_b (self,mock_eigenvalue_solve,mock_zip):
        mock_self = self.create_mock_self_for_contribution()
        idx = 1
        label = 'b'
        mock_zip.return_value = [[idx,label]]
        StraightBeam.decompose_and_quantify_eigenmodes(mock_self) 
        self.assertEqual(mock_self.decomposed_eigenmodes['rel_contribution'][0],{label: mock_self.charact_length * linalg.norm(mock_self.eigen_modes_raw[idx:(13+idx):6][:,0])})
        self.assertIsNone(np.testing.assert_allclose(mock_self.decomposed_eigenmodes['rel_contribution'][0][label], mock_self.contribution_matlab_solution[idx]))

    @mock.patch('builtins.zip')
    @mock.patch('source.model.structure_model.StraightBeam.eigenvalue_solve')
    def test_contribution_2_g (self,mock_eigenvalue_solve,mock_zip):
        mock_self = self.create_mock_self_for_contribution()
        idx = 2
        label = 'g'
        mock_zip.return_value = [[idx,label]]
        StraightBeam.decompose_and_quantify_eigenmodes(mock_self) 
        self.assertEqual(mock_self.decomposed_eigenmodes['rel_contribution'][0],{label: mock_self.charact_length * linalg.norm(mock_self.eigen_modes_raw[idx:(13+idx):6][:,0])})
        self.assertIsNone(np.testing.assert_allclose(mock_self.decomposed_eigenmodes['rel_contribution'][0][label], mock_self.contribution_matlab_solution[idx]))


    @mock.patch('builtins.zip')
    @mock.patch('source.model.structure_model.StraightBeam.eigenvalue_solve')
    def test_contribution_3_x (self,mock_eigenvalue_solve,mock_zip):
        mock_self = self.create_mock_self_for_contribution()
        idx = 3
        label = 'x'
        mock_zip.return_value = [[idx,label]]
        StraightBeam.decompose_and_quantify_eigenmodes(mock_self) 
        self.assertEqual(mock_self.decomposed_eigenmodes['rel_contribution'][0],{label: linalg.norm(mock_self.eigen_modes_raw[idx:(13+idx):6][:,0])})
        self.assertIsNone(np.testing.assert_allclose(mock_self.decomposed_eigenmodes['rel_contribution'][0][label], mock_self.contribution_matlab_solution[idx]))
   
    @mock.patch('builtins.zip')
    @mock.patch('source.model.structure_model.StraightBeam.eigenvalue_solve')
    def test_contribution_4_y (self,mock_eigenvalue_solve,mock_zip):
        mock_self = self.create_mock_self_for_contribution()
        idx = 4
        label = 'y'
        mock_zip.return_value = [[idx,label]]
        StraightBeam.decompose_and_quantify_eigenmodes(mock_self) 
        self.assertEqual(mock_self.decomposed_eigenmodes['rel_contribution'][0],{label: linalg.norm(mock_self.eigen_modes_raw[idx:(13+idx):6][:,0])})
        self.assertIsNone(np.testing.assert_allclose(mock_self.decomposed_eigenmodes['rel_contribution'][0][label], mock_self.contribution_matlab_solution[idx]))
          
    @mock.patch('builtins.zip')
    @mock.patch('source.model.structure_model.StraightBeam.eigenvalue_solve')
    def test_contribution_5_z (self,mock_eigenvalue_solve,mock_zip):
        mock_self = self.create_mock_self_for_contribution()
        idx = 5
        label = 'z'
        mock_zip.return_value = [[idx,label]]
        StraightBeam.decompose_and_quantify_eigenmodes(mock_self) 
        self.assertEqual(mock_self.decomposed_eigenmodes['rel_contribution'][0],{label: linalg.norm(mock_self.eigen_modes_raw[idx:(13+idx):6][:,0])})
        self.assertIsNone(np.testing.assert_allclose(mock_self.decomposed_eigenmodes['rel_contribution'][0][label], mock_self.contribution_matlab_solution[idx]))

    @mock.patch('builtins.zip')
    @mock.patch('source.model.structure_model.StraightBeam.eigenvalue_solve')
    def test_modal_mass_x (self,mock_eigenvalue_solve,mock_zip):
        mock_self = self.create_mock_self_for_modal_mass()
        mock_self.parameters['m'] = [1000.0,2000.0,2000.0,1000.0]
        mock_self.parameters['lz'] = [0.4, 0.4, 0.4, 0.4]
        mock_self.parameters['ly'] = [0.2, 0.2, 0.2, 0.2]
    
        # decomposed_eigenmode == 1
        # symmetric and 3 elements --> storey_mass == 1./2 * total_mass
        # numerator == total_mass
        # denominator == total_mass
        # modal_mass == total_mass
        participation = 1
        idx = 3
        label = 'x'
        mock_zip.return_value = [[idx,label]]
        StraightBeam.decompose_and_quantify_eigenmodes(mock_self) 
        self.assertIsNone(np.testing.assert_allclose(mock_self.decomposed_eigenmodes['rel_participation'][0][label],participation))

    @mock.patch('builtins.zip')
    @mock.patch('source.model.structure_model.StraightBeam.eigenvalue_solve')
    def test_modal_mass_y (self,mock_eigenvalue_solve,mock_zip):
        mock_self = self.create_mock_self_for_modal_mass()
        mock_self.parameters['m'] = [1000.0,2000.0,2000.0,1000.0]
        mock_self.parameters['lz'] = [0.4, 0.4, 0.4, 0.4]
        mock_self.parameters['ly'] = [0.2, 0.2, 0.2, 0.2]
    
        # decomposed_eigenmode == 1
        # symmetric and 3 elements --> storey_mass == 1./2 * total_mass
        # numerator == total_mass
        # denominator == total_mass
        # modal_mass == total_mass
        participation = 1
        idx = 4
        label = 'y'
        mock_zip.return_value = [[idx,label]]
        StraightBeam.decompose_and_quantify_eigenmodes(mock_self) 
        self.assertIsNone(np.testing.assert_allclose(mock_self.decomposed_eigenmodes['rel_participation'][0][label],participation))

    @mock.patch('builtins.zip')
    @mock.patch('source.model.structure_model.StraightBeam.eigenvalue_solve')
    def test_modal_mass_z (self,mock_eigenvalue_solve,mock_zip):
        mock_self = self.create_mock_self_for_modal_mass()
        mock_self.parameters['m'] = [1000.0,2000.0,2000.0,1000.0]
        mock_self.parameters['lz'] = [0.4, 0.4, 0.4, 0.4]
        mock_self.parameters['ly'] = [0.2, 0.2, 0.2, 0.2]
    
        # decomposed_eigenmode == 1
        # symmetric and 3 elements --> storey_mass == 1./2 * total_mass
        # numerator == total_mass
        # denominator == total_mass
        # modal_mass == total_mass
        participation = 1
        idx = 5
        label = 'z'
        mock_zip.return_value = [[idx,label]]
        StraightBeam.decompose_and_quantify_eigenmodes(mock_self) 
        self.assertIsNone(np.testing.assert_allclose(mock_self.decomposed_eigenmodes['rel_participation'][0][label],participation))


 
    @mock.patch('builtins.zip')
    @mock.patch('source.model.structure_model.StraightBeam.eigenvalue_solve')
    def test_modal_mass_a (self,mock_eigenvalue_solve,mock_zip):
        mock_self = self.create_mock_self_for_modal_mass()
        mock_self.parameters['m'] = [1000.0,2000.0,2000.0,1000.0]
        mock_self.parameters['lz'] = [0.4, 0.4, 0.4, 0.4]
        mock_self.parameters['ly'] = [0.2, 0.2, 0.2, 0.2]
    
        # decomposed_eigenmode == 1
        # symmetric and 3 elements --> storey_mass == 1./2 * total_mass
        # numerator == total_mass
        # denominator == total_mass
        # modal_mass == total_mass
        participation = 1
        idx = 0
        label = 'a'
        mock_zip.return_value = [[idx,label]]
        StraightBeam.decompose_and_quantify_eigenmodes(mock_self) 
        self.assertIsNone(np.testing.assert_allclose(mock_self.decomposed_eigenmodes['rel_participation'][0][label],participation))


    @mock.patch('builtins.zip')
    @mock.patch('source.model.structure_model.StraightBeam.eigenvalue_solve')
    def test_modal_mass_b (self,mock_eigenvalue_solve,mock_zip):
        mock_self = self.create_mock_self_for_modal_mass()
        mock_self.parameters['m'] = [1000.0,2000.0,2000.0,1000.0]
        mock_self.parameters['lz'] = [0.4, 0.4, 0.4, 0.4]
        mock_self.parameters['ly'] = [0.2, 0.2, 0.2, 0.2]
    
        # decomposed_eigenmode == 1
        # symmetric and 3 elements --> storey_mass == 1./2 * total_mass
        # numerator == total_mass
        # denominator == total_mass
        # modal_mass == total_mass
        # Currently participation set to 0 
        participation = 0.
        idx = 1
        label = 'b'
        mock_zip.return_value = [[idx,label]]
        StraightBeam.decompose_and_quantify_eigenmodes(mock_self) 
        self.assertIsNone(np.testing.assert_allclose(mock_self.decomposed_eigenmodes['rel_participation'][0][label],participation))
        
    @mock.patch('builtins.zip')
    @mock.patch('source.model.structure_model.StraightBeam.eigenvalue_solve')
    def test_modal_mass_g (self,mock_eigenvalue_solve,mock_zip):
        mock_self = self.create_mock_self_for_modal_mass()
        mock_self.parameters['m'] = [1000.0,2000.0,2000.0,1000.0]
        mock_self.parameters['lz'] = [0.4, 0.4, 0.4, 0.4]
        mock_self.parameters['ly'] = [0.2, 0.2, 0.2, 0.2]
    
        # decomposed_eigenmode == 1
        # symmetric and 3 elements --> storey_mass == 1./2 * total_mass
        # numerator == total_mass
        # denominator == total_mass
        # modal_mass == total_mass
        # Currently participation set to 0 
        participation = 0
        idx = 2
        label = 'g'
        mock_zip.return_value = [[idx,label]]
        StraightBeam.decompose_and_quantify_eigenmodes(mock_self) 
        self.assertIsNone(np.testing.assert_allclose(mock_self.decomposed_eigenmodes['rel_participation'][0][label],participation))

    @mock.patch('source.model.structure_model.StraightBeam.eigenvalue_solve')
    def test_modal_mass_values_symmetric (self, mock_eigenvalue_solve):
        mock_self = self.create_mock_self_for_modal_mass()
        mock_self.parameters['m'] = [1000.0,2000.0,2000.0,1000.0]
        mock_self.parameters['lz'] = [0.4, 0.4, 0.4, 0.4]
        mock_self.parameters['ly'] = [0.2, 0.2, 0.2, 0.2]

        matlab_reference_results = {
            'a': 10815.2259890856,
            'b': 0,
            'g': 0,
            'x': 3224.79725690119,
            'y': 5000.00000000000,
            'z': 5000}
        
        StraightBeam.decompose_and_quantify_eigenmodes(mock_self) 
        for label in ['x', 'y', 'z', 'a', 'b', 'g']:
            self.assertIsNone(np.testing.assert_allclose(mock_self.decomposed_eigenmodes['rel_participation'][0][label],matlab_reference_results[label]))

    @mock.patch('source.model.structure_model.StraightBeam.eigenvalue_solve')
    def test_modal_mass_values_nonsymmetric (self, mock_eigenvalue_solve):
        mock_self = self.create_mock_self_for_modal_mass()
        mock_self.parameters['m'] = [1000.0,2000.0,3000.0,4000.0]
        mock_self.parameters['lz'] = [0.4, 0.4, 0.4, 0.4]
        mock_self.parameters['ly'] = [0.2, 0.2, 0.2, 0.2]

        matlab_reference_results = {
            'a': 16222.8389836285,
            'b': 0,
            'g': 0,
            'x': 4837.19588535178,
            'y': 7500.00000000000,
            'z': 7500}
        
        StraightBeam.decompose_and_quantify_eigenmodes(mock_self) 
        for label in ['x', 'y', 'z', 'a', 'b', 'g']:
            self.assertIsNone(np.testing.assert_allclose(mock_self.decomposed_eigenmodes['rel_participation'][0][label],matlab_reference_results[label]))


if __name__ == "__main__":
    unittest.main()   