import numpy as np


class Element(object):
    def __init__(self, material_params, element_params, nodal_coords, index, domain_size):
        self.material_params = material_params
        self.domain_size = domain_size

        self.isNonlinear = material_params['is_nonlinear']

        # nodal index - defined along the x axis
        self.index = index

        # material properties
        self.E = self.material_params['e']
        self.rho = self.material_params['rho']
        self.nu = self.material_params['nu']

        # area
        self.A = element_params['a']
        # effective area of shear
        self.Asy = element_params['asy']
        self.Asz = element_params['asz']

        # second moment of inertia
        self.Iy = element_params['iy']
        self.Iz = element_params['iz']
        # torsion constant J
        self.It = element_params['it']

        # element properties
        self.NumberOfNodes = 2
        self.Dimension = 3
        self.LocalSize = self.NumberOfNodes * self.Dimension
        self.ElementSize = self.LocalSize * 2

        # element geometry
        # element geometry Node A, Node B
        self.ReferenceCoords = nodal_coords.reshape(self.LocalSize)
        # element current nodal positions
        self.CurrentCoords = self.ReferenceCoords
        # reference length of one element
        self.L = self._calculate_reference_length()

        # nonlinear elements needs the nodal forces and deformations for the geometric stiffness calculation
        if self.isNonlinear:
            # nodal forces
            self.qe = np.zeros(self.ElementSize)
            # [A_disp_x, B_disp_x, A_disp_y, B_disp_y, ... rot ..]
            # placeholder for one time step deformation to calculate the increment
            self.current_deformation = np.zeros(self.ElementSize)
            self.previous_deformation = np.zeros(self.ElementSize)

    def _print_element_information(self):
        if self.isNonlinear:
            msg = "Nonlinear "
        else:
            msg = "Linear "
        msg += str(self.domain_size) + " Base Class Element " + str(self.index) + "\n"
        print(msg)

    def update_nodal_information(self, deformation):
        self.previous_deformation = self.current_deformation
        self.current_deformation = deformation

    def evaluate_torsional_inertia(self):
        # polar moment of inertia
        # assuming equivalency with circle
        self.Ip = self.Iy + self.Iz

    def evaluate_relative_importance_of_shear(self):
        self.G = self.E / 2 / (1 + self.nu)
        # relative importance of the shear deformation to the bending one
        self.Py = 12 * self.E * self.Iz / (self.G * self.Asy * self.L ** 2)
        self.Pz = 12 * self.E * self.Iy / (self.G * self.Asz * self.L ** 2)

    def get_element_stiffness_matrix(self):
        ke = self._get_element_stiffness_matrix_material()

        if self.isNonlinear:
            ke += self._get_element_stiffness_matrix_geometry()

        return ke

    def _get_element_stiffness_matrix_material(self):
        pass

    def _get_element_stiffness_matrix_geometry(self):
        pass

    def get_element_mass_matrix(self):
        pass

    def _calculate_reference_length(self):
        dx = self.ReferenceCoords[0] - self.ReferenceCoords[3]
        dy = self.ReferenceCoords[1] - self.ReferenceCoords[4]
        dz = self.ReferenceCoords[2] - self.ReferenceCoords[5]
        length = np.sqrt(dx * dx + dy * dy + dz * dz)
        return length
