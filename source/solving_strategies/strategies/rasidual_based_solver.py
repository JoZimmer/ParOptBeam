# ===============================================================================
"""
        Derived classes from Solver

Created on:  15.10.2019
Last update: 16.10.2019
"""
# ===============================================================================

from source.solving_strategies.strategies.solver import Solver
from source.auxiliary.global_definitions import *
import numpy as np

# TODO: take these values as user input
# stopping criteria
TOL = 1.e-12
# maximum iteration
MAX_IT = 10


class ResidualBasedSolver(Solver):

    def __init__(self, array_time, time_integration_scheme, dt,
                 comp_model, initial_conditions, force, structure_model):
        super().__init__(array_time, time_integration_scheme, dt,
                         comp_model, initial_conditions, force, structure_model)

    def calculate_residual(self, q):
        pass

    def calculate_increment(self, ru):
        pass

    def solve_single_step(self):
        f_ext = self.force[:, self.step]
        self.scheme.solve_single_step(f_ext)

        nr_it = 0
        ru = 1.0
        while abs(np.max(ru)) > TOL and nr_it < MAX_IT:
            ru = self.calculate_residual(f_ext)
            du = self.calculate_increment(ru)
            self.scheme.apply_increment(du)
            print("Nonlinear iteration: ", str(nr_it))
            print("ru = {:.2e}".format(abs(np.max(ru))))
            nr_it += 1

    def solve(self):
        # time loop
        for i in range(0, len(self.array_time)):
            self.step = i
            current_time = self.array_time[i]
            print("time: {0:.2f}".format(current_time))

            self.solve_single_step()
            self.K = self.structure_model.update_stiffness_matrix()

            # appending results to the list
            self.displacement[:, i] = self.scheme.get_displacement()
            self.velocity[:, i] = self.scheme.get_velocity()
            self.acceleration[:, i] = self.scheme.get_acceleration()

            # updating deformation and reaction in the element
            for e in self.structure_model.elements:
                e.Iteration += 1
                e.update_nodal_information(
                    self.displacement[DOFS_PER_NODE[e.domain_size] * e.index:
                                      DOFS_PER_NODE[e.domain_size] * e.index +
                                      DOFS_PER_NODE[e.domain_size] * NODES_PER_LEVEL, i])

            # update results
            self.scheme.update()
