import numpy as np
from pyquaternion import Quaternion
import sys

from source.element.Element import Element

EPSILON = sys.float_info.epsilon


def apply_transformation(transformation_matrix, M):
    # transformation M = T * M * trans(T)
    aux_matrix = np.matmul(transformation_matrix, M)
    M_transformed = np.matmul(aux_matrix, transformation_matrix.T)
    return M_transformed


class CRBeamElement(Element):
    def __init__(self, material_params, element_params, nodal_coords, index, domain_size):
        if domain_size == '2D':
            err_msg = "2D CR-Beam element not implemented"
            err_msg += "Please use only 3D CR-Beam element"
            raise Exception(err_msg)

        super().__init__(material_params, element_params, nodal_coords, index, domain_size)

        self.evaluate_relative_importance_of_shear()

        # transformation matrix T = [nx0, ny0, nz0]
        self.LocalReferenceRotationMatrix = self._calculate_initial_local_cs()
        # transformation matrix T = [nx, ny, nz]
        self.LocalRotationMatrix = np.zeros([self.Dimension, self.Dimension])
        # transformation matrix
        self.TransformationMatrix = np.zeros([self.ElementSize, self.ElementSize])

        # deformation modes v = [phi_s_x, phi_s_y, phi_s_z, u phi_a_y, phi_a_z]
        self.v = np.zeros(self.LocalSize)
        # symmetric part of vector v
        self.phi_s = np.zeros(self.Dimension)
        # anti-symmetric part of vector v
        self.phi_a = np.zeros(self.Dimension)

        # for calculating deformation
        self.rA_vec = np.zeros(self.Dimension)
        self.rB_vec = np.zeros(self.Dimension)
        self.rA_sca = 1.0
        self.rB_sca = 1.0

        # initializing transformation matrix for iteration = 0
        self._update_rotation_matrix_local()
        self.TransformationMatrix = self._assemble_small_in_big_matrix(self.LocalReferenceRotationMatrix)

        # initializing bisector and vector_difference for calculating phi_a and phi_s
        self.Bisector = np.zeros(self.Dimension)
        self.VectorDifferences = np.zeros(self.Dimension)

        # incremental update
        self.incremental_deformation = np.zeros(self.ElementSize)

        self._print_element_information()

    def _print_element_information(self):
        if self.isNonlinear:
            msg = "Nonlinear "
        else:
            msg = "Linear "
        msg += str(self.domain_size) + " Co-Rotational Beam Element " + str(self.index) + "\n"
        msg += "Initial coordinates: \n"
        msg += str(self.ReferenceCoords[:3]) + "\n"
        msg += str(self.ReferenceCoords[3:]) + "\n"
        msg += "L: " + str(self.L) + "\n"
        msg += "A: " + str(self.A) + "\n"
        msg += "Asy: " + str(self.Asy) + "\n"
        msg += "Asz: " + str(self.Asz) + "\n"
        msg += "Iy: " + str(self.Iy) + "\n"
        msg += "Iz: " + str(self.Iz) + "\n"
        print(msg)

    def update_internal_force(self):
        self._update_rotation_matrix_local()
        # update local nodal force
        self._calculate_local_nodal_forces()
        self._calculate_transformation_matrix()
        self.nodal_force_global = np.dot(self.TransformationMatrix, self.nodal_force_local)

    def get_element_mass_matrix(self):
        MassMatrix = self._get_consistent_mass_matrix()
        TransformedMassMatrix = apply_transformation(self.TransformationMatrix, MassMatrix)
        return TransformedMassMatrix

    def _get_consistent_mass_matrix(self):
        """
            there are two options for mass matrix calculation, either the consistent mass matrix or the lumped mass matrix
            here the consistent mass matrix is calculated because the lumped mass matrix is singular for beam elements
        """
        MassMatrix = np.zeros([self.ElementSize, self.ElementSize])
        L2 = self.L * self.L
        Phiz = (12.0 * self.E * self.Iz) / (L2 * self.G * self.Asy)
        Phiy = (12.0 * self.E * self.Iy) / (L2 * self.G * self.Asz)

        # rotational inertia
        IRy = self.Iy
        IRz = self.Iz

        CTy = (self.rho * self.A * self.L) / ((1 + Phiy) * (1 + Phiy))
        CTz = (self.rho * self.A * self.L) / ((1 + Phiz) * (1 + Phiz))
        CRy = (self.rho * IRy) / ((1 + Phiy) * (1 + Phiy) * self.L)
        CRz = (self.rho * IRz) / ((1 + Phiz) * (1 + Phiz) * self.L)

        # longitudinal forces + torsional moment
        M00 = (1.0 / 3.0) * self.A * self.rho * self.L
        M06 = M00 / 2.0
        M33 = (self.It * self.L * self.rho) / 3.0
        M39 = M33 / 2.0

        MassMatrix[0, 0] = M00
        MassMatrix[0, 6] = M06
        MassMatrix[6, 6] = M00
        MassMatrix[3, 3] = M33
        MassMatrix[3, 9] = M39
        MassMatrix[9, 9] = M33

        temp_bending_mass_matrix = self.build_single_mass_matrix(Phiz, CTz, CRz, self.L, +1)

        MassMatrix[1, 1] = temp_bending_mass_matrix[0, 0]
        MassMatrix[1, 5] = temp_bending_mass_matrix[0, 1]
        MassMatrix[1, 7] = temp_bending_mass_matrix[0, 2]
        MassMatrix[1, 11] = temp_bending_mass_matrix[0, 3]
        MassMatrix[5, 5] = temp_bending_mass_matrix[1, 1]
        MassMatrix[5, 7] = temp_bending_mass_matrix[1, 2]
        MassMatrix[5, 11] = temp_bending_mass_matrix[1, 3]
        MassMatrix[7, 7] = temp_bending_mass_matrix[2, 2]
        MassMatrix[7, 11] = temp_bending_mass_matrix[2, 3]
        MassMatrix[11, 11] = temp_bending_mass_matrix[3, 3]

        temp_bending_mass_matrix = self.build_single_mass_matrix(Phiy, CTy, CRy, self.L, -1)

        MassMatrix[2, 2] = temp_bending_mass_matrix[0, 0]
        MassMatrix[2, 4] = temp_bending_mass_matrix[0, 1]
        MassMatrix[2, 8] = temp_bending_mass_matrix[0, 2]
        MassMatrix[2, 10] = temp_bending_mass_matrix[0, 3]
        MassMatrix[4, 4] = temp_bending_mass_matrix[1, 1]
        MassMatrix[4, 8] = temp_bending_mass_matrix[1, 2]
        MassMatrix[4, 10] = temp_bending_mass_matrix[1, 3]
        MassMatrix[8, 8] = temp_bending_mass_matrix[2, 2]
        MassMatrix[8, 10] = temp_bending_mass_matrix[2, 3]
        MassMatrix[10, 10] = temp_bending_mass_matrix[3, 3]

        for i in range(self.ElementSize):
            for j in range(i):
                MassMatrix[j, i] = MassMatrix[i, j]

        return MassMatrix

    def build_single_mass_matrix(self, Phi, CT, CR, L, dir):
        MatSize = self.NumberOfNodes * 2
        mass_matrix = np.zeros([MatSize, MatSize])
        temp_mass_matrix = np.zeros([MatSize, MatSize])

        Phi2 = Phi * Phi
        L2 = L * L

        temp_mass_matrix[0, 0] = (13.0 / 35.0) + (7.0 / 10.0) * Phi + (1.0 / 3.0) * Phi2
        temp_mass_matrix[0, 1] = dir * ((11.0 / 210.0) + (11.0 / 210.0) * Phi + (1.0 / 24.0) * Phi2) * L
        temp_mass_matrix[0, 2] = (9.0 / 70.0) + (3.0 / 10.0) * Phi + (1.0 / 6.0) * Phi2
        temp_mass_matrix[0, 3] = -((13.0 / 420.0) + (3.0 / 40.0) * Phi + (1.0 / 24.0) * Phi2) * L * dir

        temp_mass_matrix[1, 0] = temp_mass_matrix[0, 1]
        temp_mass_matrix[1, 1] = ((1.0 / 105.0) + (1.0 / 60.0) * Phi + (1.0 / 120.0) * Phi2) * L2

        temp_mass_matrix[1, 2] = dir * ((13.0 / 420.0) + (3.0 / 40.0) * Phi + (1.0 / 24.0) * Phi2) * L
        temp_mass_matrix[1, 3] = -((1.0 / 140.0) + (1.0 / 60.0) * Phi + (1.0 / 120.0) * Phi2) * L2
        temp_mass_matrix[2, 0] = temp_mass_matrix[0, 2]
        temp_mass_matrix[2, 1] = temp_mass_matrix[1, 2]
        temp_mass_matrix[2, 2] = (13.0 / 35.0) + (7.0 / 10.0) * Phi + (1.0 / 3.0) * Phi2
        temp_mass_matrix[2, 3] = -((11.0 / 210.0) + (11.0 / 210.0) * Phi + (1.0 / 24.0) * Phi2) * L * dir
        temp_mass_matrix[3, 0] = temp_mass_matrix[0, 3]
        temp_mass_matrix[3, 1] = temp_mass_matrix[1, 3]
        temp_mass_matrix[3, 2] = temp_mass_matrix[2, 3]
        temp_mass_matrix[3, 3] = ((1.0 / 105.0) + (1.0 / 60.0) * Phi + (1.0 / 120.0) * Phi2) * L2

        temp_mass_matrix *= CT
        mass_matrix += temp_mass_matrix
        temp_mass_matrix = np.zeros([MatSize, MatSize])

        temp_mass_matrix[0, 0] = 6.0 / 5.0
        temp_mass_matrix[0, 1] = dir * ((1.0 / 10.0) - (1.0 / 2.0) * Phi) * L
        temp_mass_matrix[0, 2] = -6.0 / 5.0
        temp_mass_matrix[0, 3] = dir * ((1.0 / 10.0) - (1.0 / 2.0) * Phi) * L
        temp_mass_matrix[1, 0] = temp_mass_matrix[0, 1]
        temp_mass_matrix[1, 1] = ((2.0 / 15.0) + (1.0 / 6.0) * Phi + (1.0 / 3.0) * Phi2) * L2
        temp_mass_matrix[1, 2] = dir * ((-1.0 / 10.0) + (1.0 / 2.0) * Phi) * L
        temp_mass_matrix[1, 3] = -((1.0 / 30.0) + (1.0 / 6.0) * Phi - (1.0 / 6.0) * Phi2) * L2
        temp_mass_matrix[2, 0] = temp_mass_matrix[0, 2]
        temp_mass_matrix[2, 1] = temp_mass_matrix[1, 2]
        temp_mass_matrix[2, 2] = 6.0 / 5.0
        temp_mass_matrix[2, 3] = dir * ((-1.0 / 10.0) + (1.0 / 2.0) * Phi) * L
        temp_mass_matrix[3, 0] = temp_mass_matrix[0, 3]
        temp_mass_matrix[3, 1] = temp_mass_matrix[1, 3]
        temp_mass_matrix[3, 2] = temp_mass_matrix[2, 3]
        temp_mass_matrix[3, 3] = ((2.0 / 15.0) + (1.0 / 6.0) * Phi + (1.0 / 3.0) * Phi2) * L2

        temp_mass_matrix *= CR
        mass_matrix += temp_mass_matrix

        return mass_matrix

    def get_element_stiffness_matrix(self):
        # calculate local nodal forces
        self._calculate_local_nodal_forces()

        # resizing the matrices + create memory for LHS
        Ke = np.zeros([self.ElementSize, self.ElementSize])
        # creating LHS
        Ke += self._get_element_stiffness_matrix_material()
        Ke += self._get_element_stiffness_matrix_geometry()

        TransformedStiffnessMatrix = apply_transformation(self.TransformationMatrix, Ke)
        return TransformedStiffnessMatrix

    def _get_element_stiffness_matrix_material(self):
        """
            elastic part of the total stiffness matrix
        """
        L = self.L

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

    def _get_element_stiffness_matrix_geometry(self):
        """
            geometric part of the total stiffness matrix
        """

        N = self.nodal_force_local[6]
        Mt = self.nodal_force_local[9]
        my_A = self.nodal_force_local[4]
        mz_A = self.nodal_force_local[5]
        my_B = self.nodal_force_local[10]
        mz_B = self.nodal_force_local[11]

        L = self._calculate_current_length()
        Qy = -1.0 * (mz_A + mz_B) / L
        Qz = (my_A + my_B) / L

        ke_geo = np.zeros([self.ElementSize, self.ElementSize])

        ke_geo[0, 1] = -Qy / L
        ke_geo[0, 2] = -Qz / L
        ke_geo[0, 7] = -1.0 * ke_geo[0, 1]
        ke_geo[0, 8] = -1.0 * ke_geo[0, 2]

        ke_geo[1, 0] = ke_geo[0, 1]

        ke_geo[1, 1] = 1.2 * N / L

        ke_geo[1, 3] = my_A / L
        ke_geo[1, 4] = Mt / L

        ke_geo[1, 5] = N / 10.0

        ke_geo[1, 6] = ke_geo[0, 7]
        ke_geo[1, 7] = -1.0 * ke_geo[1, 1]
        ke_geo[1, 9] = my_B / L
        ke_geo[1, 10] = -1.0 * ke_geo[1, 4]
        ke_geo[1, 11] = ke_geo[1, 5]

        ke_geo[2, 0] = ke_geo[0, 2]
        ke_geo[2, 2] = ke_geo[1, 1]
        ke_geo[2, 3] = mz_A / L
        ke_geo[2, 4] = -1.0 * ke_geo[1, 5]
        ke_geo[2, 5] = ke_geo[1, 4]
        ke_geo[2, 6] = ke_geo[0, 8]
        ke_geo[2, 8] = ke_geo[1, 7]
        ke_geo[2, 9] = mz_B / L
        ke_geo[2, 10] = ke_geo[2, 4]
        ke_geo[2, 11] = ke_geo[1, 10]

        for i in range(3):
            ke_geo[3, i] = ke_geo[i, 3]

        ke_geo[3, 4] = (-mz_A / 3.0) + (mz_B / 6.0)
        ke_geo[3, 5] = (my_A / 3.0) - (my_B / 6.0)
        ke_geo[3, 7] = -my_A / L
        ke_geo[3, 8] = -mz_A / L
        ke_geo[3, 10] = L * Qy / 6.0
        ke_geo[3, 11] = L * Qz / 6.0

        for i in range(4):
            ke_geo[4, i] = ke_geo[i, 4]

        ke_geo[4, 4] = 2.0 * L * N / 15.0
        ke_geo[4, 7] = -Mt / L
        ke_geo[4, 8] = N / 10.0
        ke_geo[4, 9] = ke_geo[3, 10]
        ke_geo[4, 10] = -L * N / 30.0
        ke_geo[4, 11] = Mt / 2.0

        for i in range(5):
            ke_geo[5, i] = ke_geo[i, 5]

        ke_geo[5, 5] = ke_geo[4, 4]
        ke_geo[5, 7] = -N / 10.0
        ke_geo[5, 8] = -Mt / L
        ke_geo[5, 9] = ke_geo[3, 11]
        ke_geo[5, 10] = -1.0 * ke_geo[4, 11]
        ke_geo[5, 11] = ke_geo[4, 10]

        for i in range(6):
            ke_geo[6, i] = ke_geo[i, 6]

        ke_geo[6, 7] = ke_geo[0, 1]
        ke_geo[6, 8] = ke_geo[0, 2]

        for i in range(7):
            ke_geo[7, i] = ke_geo[i, 7]

        ke_geo[7, 7] = ke_geo[1, 1]
        ke_geo[7, 9] = -1.0 * ke_geo[1, 9]
        ke_geo[7, 10] = ke_geo[4, 1]
        ke_geo[7, 11] = ke_geo[2, 4]

        for i in range(8):
            ke_geo[8, i] = ke_geo[i, 8]

        ke_geo[8, 8] = ke_geo[1, 1]
        ke_geo[8, 9] = -1.0 * ke_geo[2, 9]
        ke_geo[8, 10] = ke_geo[1, 5]
        ke_geo[8, 11] = ke_geo[1, 4]

        for i in range(9):
            ke_geo[9, i] = ke_geo[i, 9]

        ke_geo[9, 10] = (mz_A / 6.0) - (mz_B / 3.0)
        ke_geo[9, 11] = (-my_A / 6.0) + (my_B / 3.0)

        for i in range(10):
            ke_geo[10, i] = ke_geo[i, 10]

        ke_geo[10, 10] = ke_geo[4, 4]

        for i in range(11):
            ke_geo[11, i] = ke_geo[i, 11]

        ke_geo[11, 11] = ke_geo[4, 4]

        return ke_geo

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
        N = self.nodal_force_local[6]
        Qy = -1.0 * (self.nodal_force_local[5] + self.nodal_force_local[11]) / l
        Qz = 1.0 * (self.nodal_force_local[4] + self.nodal_force_local[10]) / l

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
        # TODO: check which length to use, paper and implementation different
        # L = self._calculate_current_length()
        L = self.L
        phi = (12.0 * self.E * I) / (L * L * self.G * A_eff)

        # interpret input A_eff == 0 as shear stiff -> psi = 1.0
        if A_eff == 0.0:
            psi = 1.0
        else:
            psi = 1.0 / (1.0 + phi)
        return psi

    def _calculate_transformation_s(self):
        S = np.zeros([self.ElementSize, self.LocalSize])
        l = self._calculate_current_length()

        S[0, 3] = -1.0
        S[1, 5] = 2.0 / l
        S[2, 4] = -2.0 / l
        S[3, 0] = -1.0
        S[4, 1] = -1.0
        S[4, 4] = 1.0
        S[5, 2] = -1.0
        S[5, 5] = 1.0
        S[6, 3] = 1.0
        S[7, 5] = -2.0 / l
        S[8, 4] = 2.0 / l
        S[9, 0] = 1.0
        S[10, 1] = 1.0
        S[10, 4] = 1.0
        S[11, 2] = 1.0
        S[11, 5] = 1.0

        return S

    def _calculate_local_nodal_forces(self):

        # element force t
        element_forces_t = self._calculate_element_forces()

        # updating transformation matrix S
        S = self._calculate_transformation_s()
        self.nodal_force_local = np.dot(S, element_forces_t)

    def _calculate_element_forces(self):
        # reference length
        L = self.L
        # current length
        l = self._calculate_current_length()
        # symmetric deformation mode
        self.phi_s = self._calculate_symmetric_deformation_mode()
        # asymmetric deformation mode
        self.phi_a = self._calculate_antisymmetric_deformation_mode()

        self.v[3] = l - L

        self.v[0:3] = self.phi_s
        self.v[4:6] = self.phi_a[1:3]

        Kd = self._calculate_deformation_stiffness()
        element_forces_t = np.dot(Kd, self.v)
        return element_forces_t

    def _calculate_symmetric_deformation_mode(self):
        """
            this function calculates symmetric part of vector v
            reference: Eq. (4.53) Klaus
        :return: phi_s
        """
        phi_s = 4.0 * np.dot(self.LocalRotationMatrix.T, self.VectorDifferences)
        return phi_s

    def _calculate_antisymmetric_deformation_mode(self):
        """
            this function calculates anti-symmetric part of v
            reference: Eq. (4.54) Klaus
        :return: phi_a
        """
        rotated_nx = self.LocalRotationMatrix[:, 0]
        temp_vector = np.cross(rotated_nx, self.Bisector)
        phi_a = 4.0 * np.dot(self.LocalRotationMatrix.T, temp_vector)
        return phi_a

    def _update_rotation_matrix_local(self):
        """
        this function updates the local transformation matrix T = [nx, ny, nz]
        Check reference in [p.134]:
            Steen Krenk. Non-linear modeling and analysis of solids and structures.
            Cambridge Univ. Press, 2009.
        """
        increment_deformation = self._update_increment_deformation()
        d_phi_a = increment_deformation[3:6]
        d_phi_b = increment_deformation[9:12]

        # calculating quaternions
        # Eq.(4.70) Klaus
        drA_vec = 0.5 * d_phi_a
        drB_vec = 0.5 * d_phi_b
        # Eq.(4.70) Klaus
        drA_sca = np.sqrt(1.0 - np.dot(drA_vec.T, drA_vec))
        drB_sca = np.sqrt(1.0 - np.dot(drA_vec.T, drB_vec))

        # Node A
        rA_sca = self.rA_sca
        rA_vec = self.rA_vec
        self.rA_sca = drA_sca * rA_sca - np.dot(drA_vec.T, rA_vec)
        self.rA_vec = drA_sca * rA_vec + \
                      rA_sca * drA_vec + \
                      np.cross(drA_vec, rA_vec)

        # Node B
        rB_sca = self.rB_sca
        rB_vec = self.rB_vec
        self.rB_sca = drB_sca * rB_sca - np.dot(drB_vec.T, rB_vec)
        self.rB_vec = drB_sca * rB_vec + \
                      rB_sca * drB_vec + \
                      np.cross(drB_vec, rB_vec)

        # scalar part of difference quaternion
        # Eq.(4.72) Klaus
        s = 0.5 * np.sqrt(((self.rA_sca + self.rB_sca) ** 2 +
                           np.linalg.norm(self.rA_vec + self.rB_vec) ** 2))

        # mean rotation quaternion
        # Eq.(4.74) Klaus
        mean_rotation_scalar = (self.rA_sca + self.rB_sca) * 0.5 / s
        # Eq.(4.75) Klaus
        mean_rotation_vector = (self.rA_vec + self.rB_vec) * 0.5 / s

        # Eq.(4.73) Klaus
        # vector part of difference quaternion, s_vec
        self.VectorDifferences = self.rA_sca * self.rB_vec - self.rB_sca * self.rA_vec + \
                                 np.cross(self.rA_vec, self.rB_vec)
        self.VectorDifferences /= 2 * s

        # rotate initial element basis
        self.Quaternion = Quaternion(w=mean_rotation_scalar,
                                     x=mean_rotation_vector[0],
                                     y=mean_rotation_vector[1],
                                     z=mean_rotation_vector[2])
        rotated_nx = self.Quaternion.rotate(self.LocalReferenceRotationMatrix[0])
        rotated_ny = self.Quaternion.rotate(self.LocalReferenceRotationMatrix[1])
        rotated_nz = self.Quaternion.rotate(self.LocalReferenceRotationMatrix[2])

        CurrentCoords = self._get_current_nodal_position()

        # rotate basis to element axis + redefine R
        delta_x = CurrentCoords[3:6] - CurrentCoords[0:3]
        delta_x /= np.linalg.norm(delta_x)

        # vector n of Eq. (4.79) Klaus
        n = rotated_nx + delta_x
        n /= np.linalg.norm(n)

        # note that the vectors are stored column wise in matrix n_xyz, therefore transpose
        #         ┌               ┐
        #         |    |  |  |    |
        # n_xyz = |   -nx ny nz   |
        #         |    |  |  |    |
        #         └               ┘
        n_xyz = np.array([-rotated_nx, rotated_ny, rotated_nz]).T
        tmp = np.outer(n, n.T)
        tmp = (np.identity(self.Dimension) - 2 * tmp)
        n_xyz = np.dot(tmp, n_xyz)
        self.LocalRotationMatrix = n_xyz
        self.Bisector = n
        self.VectorDifference = VectorDifferences

    def _calculate_transformation_matrix(self):
        """
        This function calculates the transformation matrix to globalize/localize vectors and/or matrices
        """
        # Building the rotation matrix for the local element matrix
        self.TransformationMatrix = self._assemble_small_in_big_matrix(self.LocalRotationMatrix)

    def _assemble_small_in_big_matrix(self, small_matrix):
        numerical_limit = EPSILON
        big_matrix = np.zeros([self.ElementSize, self.ElementSize])

        for k in range(0, self.ElementSize, self.Dimension):
            for i in range(self.Dimension):
                for j in range(self.Dimension):
                    if abs(small_matrix[i, j]) <= numerical_limit:
                        big_matrix[i + k, j + k] = 0.0
                    else:
                        big_matrix[i + k, j + k] = small_matrix[i, j]
        return big_matrix

    def _calculate_initial_local_cs(self):
        direction_vector_x = np.zeros(self.Dimension)

        for i in range(self.Dimension):
            direction_vector_x[i] = (self.ReferenceCoords[i + self.Dimension] - self.ReferenceCoords[i])

        # no user defined local axis 2 input available
        theta_custom = 0.0
        global_z = np.zeros(self.Dimension)
        global_z[2] = 1.0

        v2 = np.zeros(self.Dimension)
        v3 = np.zeros(self.Dimension)

        vector_norm = np.linalg.norm(direction_vector_x)
        if vector_norm > EPSILON:
            direction_vector_x /= vector_norm

        if np.linalg.norm(direction_vector_x[2] - 1.0) < EPSILON:
            v2[1] = 1.0
            v3[0] = -1.0
        elif np.linalg.norm(direction_vector_x[2] + 1.0) < EPSILON:
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

        reference_transformation = np.array([direction_vector_x, v2, v3])

        return reference_transformation
