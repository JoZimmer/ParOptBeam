import numpy as np

from source.scheme.time_integration_scheme import TimeIntegrationScheme


class RungeKutta4(TimeIntegrationScheme):
    """
    (Explicit) Runge Kutta 4th order approximation

    """

    def __init__(self, dt, comp_model, initial_conditions):
        # introducing and initializing properties and coefficients
        # construct an object self with the input arguments dt, M, B, K,
        # pInf, u0, v0, a0

        # time step
        self.dt = dt

        # mass, damping and spring stiffness
        self.M = comp_model[0]
        self.B = comp_model[1]
        self.K = comp_model[2]

        # inverse matrix
        self.InvM = np.linalg.inv(self.M)

        # structure
        # initial displacement, velocity and acceleration
        self.u0 = initial_conditions[0]
        self.v0 = initial_conditions[1]
        self.a0 = initial_conditions[2]

        # initial displacement, velocity and acceleration
        self.un1 = self.u0
        self.vn1 = self.v0
        self.an1 = self.a0

        # force from a previous time step (initial force)
        self.f0 = np.dot(self.M, self.a0) + np.dot(self.B, self.v0) + np.dot(self.K, self.u0)
        self.f1 = np.dot(self.M, self.an1) + np.dot(self.B, self.vn1) + np.dot(self.K, self.un1)

        self._print_structural_setup()
        self._print_time_integration_setup()

    def _print_time_integration_setup(self):
        print("Printing Runge Kutta 4th order approximation integration scheme setup:")
        print("dt: ", self.dt)
        print(" ")

    def solve_structure(self, f1):

        # calculates self.un0,vn0,an0
        f_mid = (f1 + self.f1) / 2.0

        k0 = self.dt * self.vn1
        l0 = self.dt * np.dot(self.InvM, (-np.dot(self.B, self.vn1) - np.dot(self.K, self.un1) + self.f1))

        k1 = self.dt * (0.5*l0 + self.vn1)
        l1 = self.dt * np.dot(self.InvM, (-np.dot(self.B, (0.5*l0 + self.vn1)) - np.dot(self.K, (0.5*k0 + self.un1)) + f_mid))
        k2 = self.dt * (0.5*l1 + self.vn1)
        l2 = self.dt * np.dot(self.InvM, (-np.dot(self.B, (0.5*l1 + self.vn1)) - np.dot(self.K, (0.5*k1 + self.un1)) + f_mid))
        k3 = self.dt * (l2 + self.vn1)
        l3 = self.dt * np.dot(self.InvM, (-np.dot(self.B, (l2 + self.vn1)) - np.dot(self.K, (k2 + self.un1)) + f1))

        # update self.u1,v1,a1
        self.u1 = self.un1 + (k0 + 2*(k1 + k2) + k3)/6.0
        self.v1 = self.vn1 + (l0 + 2*(l1 + l2) + l3)/6.0
        self.a1 = (self.v1 - self.vn1)/self.dt

        # update self.f1
        self.f1 = f1

        if np.isnan(np.min(self.u1)):
            print("NaN found in displacement!")

    def update_structure_time_step(self):
        # update self.un2 un1
        self.un1 = self.u1
        self.vn1 = self.v1
        self.an1 = self.a1


