import numpy as np

from source.element.Element import Element


class CRBeamElement(Element):
    def __init__(self, parameters, domain_size):
        super().__init__(parameters, domain_size)

        # element properties

        self.E = self.parameters['e']
        self.L = self.parameters['lx_i']

        # area
        self.A = self.parameters['a']
        # effective area of shear
        self.Ay = self.parameters['a_sy']
        self.Az = self.parameters['a_sz']
        # second moment of inertia
        self.Iy = self.parameters['iy']
        self.Iz = self.parameters['iz']

        self._print_element_information()

    def _print_element_information(self):
        print(str(self.domain_size), "D Co-Rotational Beam Element")

    def get_el_mass(self, i):
        """
            element mass matrix derivation from Klaus Bernd Sautter's master thesis
        """

    def get_el_stiffness(self, i):
        """
            element stiffness matrix derivation from Klaus Bernd Sautter's master thesis
        """


        phi_a_y = 1 / (1 + 12 * E * Iy / (L ** 2 * G * Az))
        phi_a_z = 1 / (1 + 12 * E * Iz / (L ** 2 * G * Ay))

        # constant stiffness
        kc_11 = np.array([[E * A / L, 0, 0],
                          [0, 12 * E * Iz * phi_a_z / L ** 3, 0],
                          [0, 12 * E * Iy * phi_a_y / L ** 3, 0]])
