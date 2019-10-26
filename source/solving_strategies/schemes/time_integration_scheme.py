# ===============================================================================
'''
Project:Lecture - Structural Wind Engineering WS17-18 
        Chair of Structural Analysis @ TUM - A. Michalski, R. Wuchner, M. Pentek
        
        Time integration scheme base class and derived classes for specific implementations

Author: mate.pentek@tum.de, anoop.kodakkal@tum.de, klaus.sautter@tum.de


      
Note:   UPDATE: The script has been written using publicly available information and 
        data, use accordingly. It has been written and tested with Python 2.7.9.
        Tested and works also with Python 3.4.3 (already see differences in print).
        Module dependencies (-> line 61-74): 
            python
            numpy
            sympy
            matplotlib.pyplot

Created on:  22.11.2017
Last update: 09.07.2019
'''
# ===============================================================================


import numpy as np


class TimeIntegrationScheme(object):
    def __init__(self, dt, comp_model, initial_conditions):
        # time step
        self.dt = dt

        # mass, damping and spring stiffness
        self.M = comp_model[0]
        self.B = comp_model[1]
        self.K = comp_model[2]

        # initial displacement, velocity and acceleration
        self.u0 = initial_conditions[0]
        self.v0 = initial_conditions[1]
        self.a0 = initial_conditions[2]

        # initial previous step displacement, velocity and acceleration
        self.un1 = self.u0
        self.vn1 = self.v0
        self.an1 = self.a0

        # initial current step displacement, velocity and acceleration
        self.u1 = self.u0
        self.v1 = self.v0
        self.a1 = self.a0

        # force from a previous time step (initial force)
        self.f0 = None
        self.f1 = None

    def _print_time_integration_setup(self):
        pass

    def predict_displacement(self):
        return 2.0 * self.u1 - self.u0

    def predict_velocity(self, u1):
        pass

    def predict_acceleration(self, v1):
        pass

    def solve_single_step(self, f1):
        pass

    def print_values_at_current_step(self, n):
        print("Printing values at step no: ", n, " (+1)")
        print("u0: ", self.u1)
        print("v0: ", self.v1)
        print("a0: ", self.a1)
        print("f0: ", self.f1)
        print(" ")

    def get_displacement(self):
        return self.u1

    def get_velocity(self):
        return self.v1

    def get_acceleration(self):
        return self.a1

    def get_old_displacement(self):
        return self.un1

    def get_old_velocity(self):
        return self.vn1

    def get_old_acceleration(self):
        return self.an1
