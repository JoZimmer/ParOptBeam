import numpy as np
import sys

from source.element.Element import Element

EPSILON = sys.float_info.epsilon


def rotate_vector(quaternion, vector):
    b0 = 2.0 * (quaternion[1] * vector[2] - quaternion[2] * vector[1])
    b1 = 2.0 * (quaternion[2] * vector[0] - quaternion[0] * vector[2])
    b2 = 2.0 * (quaternion[0] * vector[1] - quaternion[1] * vector[0])

    c0 = quaternion[1] * b2 - quaternion[2] * b1
    c1 = quaternion[2] * b0 - quaternion[0] * b2
    c2 = quaternion[0] * b1 - quaternion[1] * b0

    vector[0] += b0 * quaternion[3] + c0
    vector[1] += b1 * quaternion[3] + c1
    vector[2] += b2 * quaternion[3] + c2

    return vector


class CRBeamElement(Element):
    def __init__(self, material_params, element_params, nodal_coords, domain_size):
        super().__init__(material_params, domain_size)

        # material properties
        self.E = self.parameters['e']
        self.rho = self.parameters['rho']
        self.nu = self.parameters['nu']
        self.G = self.parameters['g'] = self.E / 2 / (1 + self.nu)

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

        # [A_disp_x, B_disp_x, A_disp_y, B_disp_y, ... rot ..]
        # placeholder for one time step deformation to calculate the increment
        self.current_deformation = np.zeros(self.ElementSize)
        self.previous_deformation = np.zeros(self.ElementSize)

        self.Iteration = 0

        # nodal forces
        self.qe = np.zeros(self.ElementSize)

        # transformation matrix
        self.S = np.zeros([self.ElementSize, self.LocalSize])
        self.LocalRotationMatrix = np.zeros(self.Dimension)
        self.TransformationMatrix = np.zeros([self.ElementSize, self.ElementSize])
        self.Bisectrix = np.zeros(self.Dimension)
        self.VectorDifferences = np.zeros(self.Dimension)

        # for calculating deformation
        self._QuaternionVEC_A = np.zeros(self.Dimension)
        self._QuaternionVEC_B = np.zeros(self.Dimension)
        self._QuaternionSCA_A = 1.0
        self._QuaternionSCA_B = 1.0

        self._print_element_information()

    def _print_element_information(self):
        msg = str(self.domain_size) + " Co-Rotational Beam Element\n"
        msg += "Element Size: " + str(self.ElementSize) + "\n"
        print(msg)

    def get_el_mass(self, i):
        """
            element mass matrix derivation from Klaus Bernd Sautter's master thesis
        """

    def get_el_stiffness(self, i):
        """
            element stiffness matrix derivation from Klaus Bernd Sautter's master thesis
        """
        pass

    def get_left_hand_side(self):
        if self.Iteration == 0:
            self.TransformationMatrix = self._calculate_initial_local_cs()
        else:
            self.TransformationMatrix = self._calculate_transformation_matrix()

        # calculate local nodal forces
        self._calculate_local_nodal_forces()

    def _get_local_stiffness_matrix_material(self):
        """
            elastic part of the total stiffness matrix
        """
        L = self._calculate_current_length()

        # shear coefficients
        Psi_y = self._calculate_psi(self.Iy, self.Asz)
        Psi_z = self._calculate_psi(self.Iz, self.Asy)

        ke_const = np.zeros([self.ElementSize, self.ElementSize])

        self.L3 = L * L * L
        self.L2 = L * L

        ke_const[0, 0] = self.E * self.A / L
        ke_const[6, 0] = -1.0 * ke_const[0, 0]
        ke_const[0, 6] = ke_const[6, 0]
        ke_const[6, 6] = ke_const[0, 0]

        ke_const[1, 1] = 12.0 * self.E * self.Iz * Psi_z / self.L3
        ke_const[1, 7] = -1.0 * ke_const[1, 1]
        ke_const[1, 5] = 6.0 * self.E * self.Iz * Psi_z / self.L2
        ke_const[1, 11] = ke_const[1, 5]

        ke_const[2, 2] = 12.0 * self.E * self.Iy * Psi_y / self.L3
        ke_const[2, 8] = -1.0 * ke_const[2, 2]
        ke_const[2, 4] = -6.0 * self.E * self.Iy * Psi_y / self.L2
        ke_const[2, 10] = ke_const[2, 4]

        ke_const[4, 2] = ke_const[2, 4]
        ke_const[5, 1] = ke_const[1, 5]
        ke_const[3, 3] = self.G * self.It / L
        ke_const[4, 4] = self.E * self.Iy * (3.0 * Psi_y + 1.0) / L
        ke_const[5, 5] = self.E * self.Iz * (3.0 * Psi_z + 1.0) / L
        ke_const[4, 8] = -1.0 * ke_const[4, 2]
        ke_const[5, 7] = -1.0 * ke_const[5, 1]
        ke_const[3, 9] = -1.0 * ke_const[3, 3]
        ke_const[4, 10] = self.E * self.Iy * (3.0 * Psi_y - 1.0) / L
        ke_const[5, 11] = self.E * self.Iz * (3.0 * Psi_z - 1.0) / L

        ke_const[7, 1] = ke_const[1, 7]
        ke_const[7, 5] = ke_const[5, 7]
        ke_const[7, 7] = ke_const[1, 1]
        ke_const[7, 11] = ke_const[7, 5]

        ke_const[8, 2] = ke_const[2, 8]
        ke_const[8, 4] = ke_const[4, 8]
        ke_const[8, 8] = ke_const[2, 2]
        ke_const[8, 10] = ke_const[8, 4]

        ke_const[9, 3] = ke_const[3, 9]
        ke_const[9, 9] = ke_const[3, 3]

        ke_const[10, 2] = ke_const[2, 10]
        ke_const[10, 4] = ke_const[4, 10]
        ke_const[10, 8] = ke_const[8, 10]
        ke_const[10, 10] = ke_const[4, 4]

        ke_const[11, 1] = ke_const[1, 11]
        ke_const[11, 5] = ke_const[5, 11]
        ke_const[11, 7] = ke_const[7, 11]
        ke_const[11, 11] = ke_const[5, 5]

        return ke_const

    def _get_local_stiffness_matrix_geometry(self):
        """
            geometric part of the total stiffness matrix
        """

        N = self.qe[6]
        Mt = self.qe[9]
        my_A = self.qe[4]
        mz_A = self.qe[5]
        my_B = self.qe[10]
        mz_B = self.qe[11]

        L = self._calculate_current_length()
        Qy = -1.00 * (mz_A + mz_B) / L
        Qz = (my_A + my_B) / L

        kg_const = np.zeros([self.ElementSize, self.ElementSize])

        kg_const[0, 1] = -Qy / L
        kg_const[0, 2] = -Qz / L
        kg_const[0, 7] = -1.0 * kg_const[0, 1]
        kg_const[0, 8] = -1.0 * kg_const[0, 2]

        kg_const[1, 0] = kg_const[0, 1]

        kg_const[1, 1] = 1.2 * N / L

        kg_const[1, 3] = my_A / L
        kg_const[1, 4] = Mt / L

        kg_const[1, 5] = N / 10.0

        kg_const[1, 6] = kg_const[0, 7]
        kg_const[1, 7] = -1.00 * kg_const[1, 1]
        kg_const[1, 9] = my_B / L
        kg_const[1, 10] = -1.00 * kg_const[1, 4]
        kg_const[1, 11] = kg_const[1, 5]

        kg_const[2, 0] = kg_const[0, 2]
        kg_const[2, 2] = kg_const[1, 1]
        kg_const[2, 3] = mz_A / L
        kg_const[2, 4] = -1.00 * kg_const[1, 5]
        kg_const[2, 5] = kg_const[1, 4]
        kg_const[2, 6] = kg_const[0, 8]
        kg_const[2, 8] = kg_const[1, 7]
        kg_const[2, 9] = mz_B / L
        kg_const[2, 10] = kg_const[2, 4]
        kg_const[2, 11] = kg_const[1, 10]

        for i in range(3):
            kg_const[3, i] = kg_const[i, 3]

        kg_const[3, 4] = (-mz_A / 3.00) + (mz_B / 6.00)
        kg_const[3, 5] = (my_A / 3.00) - (my_B / 6.00)
        kg_const[3, 7] = -my_A / L
        kg_const[3, 8] = -mz_A / L
        kg_const[3, 10] = L * Qy / 6.00
        kg_const[3, 11] = L * Qz / 6.00

        for i in range(4):
            kg_const[4, i] = kg_const[i, 4]

        kg_const[4, 4] = 2.00 * L * N / 15.00
        kg_const[4, 7] = -Mt / L
        kg_const[4, 8] = N / 10.00
        kg_const[4, 9] = kg_const[3, 10]
        kg_const[4, 10] = -L * N / 30.00
        kg_const[4, 11] = Mt / 2.00

        for i in range(5):
            kg_const[5, i] = kg_const[i, 5]

        kg_const[5, 5] = kg_const[4, 4]
        kg_const[5, 7] = -N / 10.0
        kg_const[5, 8] = -Mt / L
        kg_const[5, 9] = kg_const[3, 11]
        kg_const[5, 10] = -1.00 * kg_const[4, 11]
        kg_const[5, 11] = kg_const[4, 10]

        for i in range(6):
            kg_const[6, i] = kg_const[i, 6]

        kg_const[6, 7] = kg_const[0, 1]
        kg_const[6, 8] = kg_const[0, 2]

        for i in range(7):
            kg_const[7, i] = kg_const[i, 7]

        kg_const[7, 7] = kg_const[1, 1]
        kg_const[7, 9] = -1.00 * kg_const[1, 9]
        kg_const[7, 10] = kg_const[4, 1]
        kg_const[7, 11] = kg_const[2, 4]

        for i in range(8):
            kg_const[8, i] = kg_const[i, 8]

        kg_const[8, 8] = kg_const[1, 1]
        kg_const[8, 9] = -1.00 * kg_const[2, 9]
        kg_const[8, 10] = kg_const[1, 5]
        kg_const[8, 11] = kg_const[1, 4]

        for i in range(9):
            kg_const[9, i] = kg_const[i, 9]

        kg_const[9, 10] = (mz_A / 6.00) - (mz_B / 3.00)
        kg_const[9, 11] = (-my_A / 6.00) + (my_B / 3.00)

        for i in range(10):
            kg_const[10, i] = kg_const[i, 10]

        kg_const[10, 10] = kg_const[4, 4]

        for i in range(11):
            kg_const[11, i] = kg_const[i, 11]

        kg_const[11, 11] = kg_const[4, 4]

        return kg_const

    def _calculate_deformation_stiffness(self):
        L = self.L
        Psi_y = self._calculate_psi(self.Iy, self.Asz)
        Psi_z = self._calculate_psi(self.Iz, self.Asy)

        Kd = np.zeros([self.LocalSize, self.LocalSize])

        Kd[0, 0] = self.G * self.It / L
        Kd[1, 1] = self.E * self.Iy / L
        Kd[2, 2] = self.E * self.Iz / L
        Kd[3, 3] = self.E * self.A / L
        Kd[4, 4] = 3.0 * self.E * self.Iy * Psi_y / L
        Kd[5, 5] = 3.0 * self.E * self.Iz * Psi_z / L

        l = self._calculate_current_length()
        N = self.qe[6]
        Qy = -1.0 * (self.qe[5] + self.qe[11]) / l
        Qz = 1.0 * (self.qe[4] + self.qe[10]) / l

        N1 = l * N / 12.0
        N2 = l * N / 20.0
        Qy1 = -l * Qy / 6.0
        Qz1 = -l * Qz / 6.0

        Kd[1, 1] += N1
        Kd[2, 2] += N1
        Kd[4, 4] += N2
        Kd[5, 5] += N2

        Kd[0, 1] += Qy1
        Kd[0, 2] += Qz1
        Kd[1, 0] += Qy1
        Kd[2, 0] += Qz1

        return Kd

    def _calculate_psi(self, I, A_eff):
        L = self._calculate_current_length()
        phi = (12.0 * self.E * I) / (L * L * self.G * A_eff)

        # interpret input A_eff == 0 as shear stiff -> psi = 1.0
        if A_eff == 0.0:
            psi = 1.0
        else:
            psi = 1.0 / (1.0 + phi)
        return psi

    def _calculate_transformation_s(self):
        L = self._calculate_current_length()

        self.S[0, 3] = -1.00
        self.S[1, 5] = 2.00 / L
        self.S[2, 4] = -2.00 / L
        self.S[3, 0] = -1.00
        self.S[4, 1] = -1.00
        self.S[4, 4] = 1.00
        self.S[5, 2] = -1.00
        self.S[5, 5] = 1.00
        self.S[6, 3] = 1.00
        self.S[7, 5] = -2.00 / L
        self.S[8, 4] = 2.00 / L
        self.S[9, 0] = 1.00
        self.S[10, 1] = 1.00
        self.S[10, 4] = 1.00
        self.S[11, 2] = 1.00
        self.S[11, 5] = 1.00

    def _calculate_local_nodal_forces(self):
        # element force t
        element_forces_t = self._calculate_element_forces()

        # updating transformation matrix S
        self._calculate_transformation_s()
        self.qe = np.dot(self.S, element_forces_t)

    def _calculate_element_forces(self):
        # reference length
        L = self.L
        # current length
        l = self._calculate_current_length()
        # symmetric deformation mode
        phi_s = np.zeros(self.Dimension)
        # asymmetric deformation mode
        phi_a = np.zeros(self.Dimension)
        rotated_nx0 = np.zeros(self.Dimension)

        if self.Iteration != 0:
            phi_s = np.dot((np.transpose(self.LocalRotationMatrix)), self.VectorDifferences)
            phi_s *= 4.0
            for i in range(0, self.Dimension):
                rotated_nx0[i] = self.LocalRotationMatrix[i, 0]
            temp_vector = np.cross(rotated_nx0, self.Bisectrix)
            phi_a = np.dot((np.transpose(self.LocalRotationMatrix)), temp_vector)
            phi_a *= 4.0

        deformation_modes_total_v = np.zeros(self.LocalSize)
        deformation_modes_total_v[3] = l - L

        for i in range(3):
            deformation_modes_total_v[i] = phi_s[i]
        for i in range(2):
            deformation_modes_total_v[i + 4] = phi_a[i + 1]

        Kd = self._calculate_deformation_stiffness()
        element_forces_t = np.dot(Kd, deformation_modes_total_v)
        return element_forces_t

    def _update_rotation_matrix_local(self):
        d_phi_a = np.zeros(self.Dimension)
        d_phi_b = np.zeros(self.Dimension)
        increment_deformation = self._update_increment_deformation()
        print(increment_deformation)
        for i in range(0, self.Dimension):
            d_phi_a[i] = increment_deformation[i + 3]
            d_phi_b[i] = increment_deformation[i + 9]

        # calculating quaternions
        drA_vec = 0.50 * d_phi_a
        drB_vec = 0.50 * d_phi_b

        drA_sca = 0.00
        drB_sca = 0.00

        for i in range(0, self.Dimension):
            drA_sca += drA_vec[i] * drA_vec[i]
            drB_sca += drB_vec[i] * drB_vec[i]

        drA_sca = np.sqrt(1.00 - drA_sca)
        drB_sca = np.sqrt(1.00 - drB_sca)

        # Node A
        temp_vec = self._QuaternionVEC_A
        temp_scalar = self._QuaternionSCA_A
        self._QuaternionVEC_A = drA_sca * temp_scalar
        for i in range(self.Dimension):
            self._QuaternionSCA_A -= drA_vec[i] * temp_vec[i]

        self._QuaternionVEC_A = drA_sca * temp_vec
        self._QuaternionVEC_A += temp_scalar * drA_vec
        self._QuaternionVEC_A += np.cross(drA_vec, temp_vec)

        # Node B
        temp_vec = self._QuaternionVEC_B
        temp_scalar = self._QuaternionSCA_B
        self._QuaternionVEC_B = drB_sca * temp_scalar
        for i in range(self.Dimension):
            self._QuaternionSCA_B -= drB_vec[i] * temp_vec[i]

        self._QuaternionVEC_B = drB_sca * temp_vec + temp_scalar * drB_vec + np.cross(drB_vec, temp_vec)

        # scalar part of difference quaternion
        scalar_diff = (self._QuaternionSCA_A + self._QuaternionSCA_B) * (self._QuaternionSCA_A + self._QuaternionSCA_B)
        temp_vec = self._QuaternionVEC_A + self._QuaternionVEC_B
        scalar_diff += np.linalg.norm(temp_vec) * np.linalg.norm(temp_vec)
        scalar_diff = 0.5 * np.sqrt(scalar_diff)

        # mean rotation quaternion
        mean_rotation_scalar = (self._QuaternionSCA_A + self._QuaternionSCA_B) * 0.50 / scalar_diff
        mean_rotation_vector = (self._QuaternionVEC_A + self._QuaternionVEC_B) * 0.50 / scalar_diff

        # vector part of difference quaternion
        self.VectorDifferences = self._QuaternionSCA_A * self._QuaternionVEC_B
        self.VectorDifferences -= self._QuaternionSCA_A * self._QuaternionVEC_A
        self.VectorDifferences += np.cross(self._QuaternionVEC_A, self._QuaternionVEC_B)

        self.VectorDifferences = 0.5 * self.VectorDifferences / scalar_diff
        # rotate initial element basis
        r0 = mean_rotation_scalar
        r1 = mean_rotation_vector[0]
        r2 = mean_rotation_vector[1]
        r3 = mean_rotation_vector[2]
        reference_transformation = self._calculate_initial_local_cs()
        rotated_nx0 = np.zeros(self.Dimension)
        rotated_ny0 = np.zeros(self.Dimension)
        rotated_nz0 = np.zeros(self.Dimension)

        for i in range(self.Dimension):
            rotated_nx0[i] = reference_transformation[i, 0]
            rotated_ny0[i] = reference_transformation[i, 1]
            rotated_nz0[i] = reference_transformation[i, 2]

        quaternion = [r0, r1, r2, r3]
        rotated_nx0 = rotate_vector(quaternion, rotated_nx0)
        rotated_ny0 = rotate_vector(quaternion, rotated_ny0)
        rotated_nz0 = rotate_vector(quaternion, rotated_nz0)

        rotated_coordinate_system = np.zeros([self.Dimension, self.Dimension])
        for i in range(self.Dimension):
            rotated_coordinate_system[i, 0] = rotated_nx0[i]
            rotated_coordinate_system[i, 1] = rotated_ny0[i]
            rotated_coordinate_system[i, 2] = rotated_nz0[i]

        # rotate basis to element axis + redefine R
        delta_x = np.zeros(self.Dimension)
        for i in range(self.Dimension):
            delta_x[i] = self.CurrentCoords[self.Dimension + i] - self.CurrentCoords[i]
        vector_norm = np.linalg.norm(delta_x)

        if vector_norm > EPSILON:
            delta_x /= vector_norm

        self.Bisectrix = rotated_nx0 + delta_x
        vector_norm = np.linalg.norm(self.Bisectrix)

        if vector_norm > EPSILON:
            self.Bisectrix /= vector_norm

        n_xyz = np.zeros([self.Dimension, self.Dimension])

        for i in range(0, self.Dimension):
            n_xyz[i, 0] = -rotated_coordinate_system[i, 0]
            n_xyz[i, 1] = rotated_coordinate_system[i, 1]
            n_xyz[i, 2] = rotated_coordinate_system[i, 2]

        Identity = np.identity(self.Dimension)
        Identity -= 2.0 * np.outer(self.Bisectrix, self.Bisectrix)

        n_xyz = np.dot(Identity, n_xyz)
        return n_xyz

    def _calculate_transformation_matrix(self):
        AuxRotationMatrix = self._update_rotation_matrix_local()
        RotationMatrix = np.zeros([self.ElementSize, self.ElementSize])
        RotationMatrix = self._assemble_small_in_big_matrix(AuxRotationMatrix, RotationMatrix)
        return RotationMatrix

    def _assemble_small_in_big_matrix(self, small_matrix, big_matrix):
        numerical_limit = EPSILON
        for k in range(0, self.ElementSize, self.Dimension):
            for i in range(self.Dimension):
                for j in range(self.Dimension):
                    if abs(small_matrix[i, j]) <= numerical_limit:
                        big_matrix[i + k, j + k] = 0.0
                    else:
                        big_matrix[i + k, j + k] = small_matrix[i, j]
        return big_matrix

    def _update_increment_deformation(self):
        """
         This function updates incremental deformation w.r.t. to current and previous deformations
        """
        increment_deformation = self.current_deformation - self.current_deformation
        return increment_deformation

    def _calculate_initial_local_cs(self):
        direction_vector_x = np.zeros(self.Dimension)

        for i in range(self.Dimension):
            direction_vector_x[i] = (self.ReferenceCoords[i + self.Dimension] - self.ReferenceCoords[i])

        temp_matrix = np.zeros([self.Dimension, self.Dimension])
        # no user defined local axis 2 input available
        theta_custom = 0.0
        global_z = np.zeros(self.Dimension)
        global_z[2] = 1.0

        v2 = np.zeros(self.Dimension)
        v3 = np.zeros(self.Dimension)

        vector_norm = np.linalg.norm(direction_vector_x)
        if vector_norm > EPSILON:
            direction_vector_x /= vector_norm

        if np.linalg.norm(direction_vector_x[2] - 1.00) < EPSILON:
            v2[1] = 1.0
            v3[0] = -1.0
        elif np.linalg.norm(direction_vector_x[2] + 1.00) < EPSILON:
            v2[1] = 1.0
            v3[0] = 1.0
        else:
            v2 = np.cross(global_z, direction_vector_x)
            v3 = np.cross(direction_vector_x, v2)

        # manual rotation around the beam axis
        if np.linalg.norm(theta_custom) > EPSILON:
            nz_temp = v3
            ny_temp = v2
            cos_theta = np.cos(theta_custom)
            sin_theta = np.sin(theta_custom)

            v2 = ny_temp * cos_theta + nz_temp * sin_theta
            vector_norm = np.linalg.norm(v2)

            if vector_norm > EPSILON:
                v2 /= vector_norm

            v3 = nz_temp * cos_theta - ny_temp * sin_theta
            vector_norm = np.linalg.norm(v3)

            if vector_norm > EPSILON:
                v3 /= vector_norm

            for i in range(self.Dimension):
                temp_matrix[i, 0] = direction_vector_x[i]
                temp_matrix[i, 1] = v2[i]
                temp_matrix[i, 2] = v3[i]

        reference_transformation = np.zeros([self.ElementSize, self.ElementSize])
        reference_transformation = self._assemble_small_in_big_matrix(temp_matrix, reference_transformation)

        return reference_transformation

    def _calculate_reference_length(self):
        dx = self.ReferenceCoords[0] - self.ReferenceCoords[1]
        dy = self.ReferenceCoords[2] - self.ReferenceCoords[3]
        dz = self.ReferenceCoords[4] - self.ReferenceCoords[5]
        length = np.sqrt(dx * dx + dy * dy + dz * dz)
        return length

    def _calculate_current_length(self):
        du = self.current_deformation[0] - self.current_deformation[1]
        dv = self.current_deformation[2] - self.current_deformation[3]
        dw = self.current_deformation[4] - self.current_deformation[5]

        print("====================================")
        print(self.ReferenceCoords)

        dx = self.ReferenceCoords[0] - self.ReferenceCoords[1]
        dy = self.ReferenceCoords[3] - self.ReferenceCoords[3]
        dz = self.ReferenceCoords[4] - self.ReferenceCoords[5]

        length = np.sqrt((du + dx) * (du + dx) + (dv + dy) * (dv + dy) + (dw + dz) * (dw + dz))
        print(length)
        return length
