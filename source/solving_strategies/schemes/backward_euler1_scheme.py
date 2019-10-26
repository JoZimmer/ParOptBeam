import numpy as np

from source.solving_strategies.schemes.time_integration_scheme import TimeIntegrationScheme


class BackwardEuler1(TimeIntegrationScheme):
    """
    (Implicit) Backward Euler 1st order approximation

    """

    def __init__(self, dt, comp_model, initial_conditions):
        # introducing and initializing properties and coefficients
        # construct an object self with the input arguments dt, M, B, K,
        # pInf, u0, v0, a0

        super().__init__(dt, comp_model, initial_conditions)

        self.LHS = self.M + self.B * self.dt + self.K * self.dt ** 2

        # initial values for time integration
        self.un1 = self.u0
        self.un2 = self.u0
        self.vn1 = self.v0
        self.an1 = self.a0

        self._print_time_integration_setup()

    def _print_time_integration_setup(self):
        print("Printing (Implicit) Backward Euler 1 st order approximation integration scheme setup:")
        print("dt: ", self.dt)
        print(" ")

    def predict_velocity(self, u1):
        v1 = (u1 - self.un1) / self.dt
        return v1

    def predict_acceleration(self, v1):
        a1 = (v1 - self.vn1) / self.dt
        return a1

    def solve_single_step(self, f1):
        # calculates self.un0,vn0,an0
        RHS = self.dt * np.dot(self.B, self.un1) + 2 * np.dot(self.M, self.un1)
        RHS += - np.dot(self.M, self.un2) + self.dt ** 2 * f1
        self.u1 = np.linalg.solve(self.LHS, RHS)
        self.v1 = self.predict_velocity(self.u1)
        self.a1 = self.predict_acceleration(self.v1)

    def calculate_increment(self, ru):
        LHS = (self.B * self.dt + self.K * self.dt**2 + self.M)
        RHS = ru * self.dt ** 2
        du = np.linalg.solve(LHS, RHS)
        return du

    def update(self):
        # update self.un2 un1
        self.un2 = self.un1
        self.un1 = self.u1
        self.vn1 = self.v1
        self.an1 = self.a1
