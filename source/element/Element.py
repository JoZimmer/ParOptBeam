import numpy as np


class Element(object):
    def __init__(self, material_params, element_params, nodal_coords, index, domain_size):
        self.material_params = material_params
        self.domain_size = domain_size

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

        # element geometry Node A, Node B
        self.ReferenceCoords = nodal_coords.reshape(self.LocalSize)
        # element current nodal positions
        self.CurrentCoords = self.ReferenceCoords
        # reference length of one element
        self.L = self._calculate_reference_length()

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
        pass

    def get_element_mass_matrix(self):
        pass

    def _print_element_information(self):
        msg = str(self.domain_size) + " Base Class Element " + str(self.index) + "\n"
        print(msg)

    def _calculate_reference_length(self):
        dx = self.ReferenceCoords[0] - self.ReferenceCoords[1]
        dy = self.ReferenceCoords[2] - self.ReferenceCoords[3]
        dz = self.ReferenceCoords[4] - self.ReferenceCoords[5]
        length = np.sqrt(dx * dx + dy * dy + dz * dz)
        return length
