################################################################################################
###   M * u''(t) + C * u'(t) + K * u(t) = f rewrite 2nd order ODE into system of 1st order ODEs
###   (I)  v'(t) = ( f - C * v(t) - K * u(t) ) / M = f(t, u, v) = rhs
###   (II) u'(t) = v(t)
###   differential equations in the form (d^2)y/(du^2) = (rhs)
###   rhs: The right-hand side function of the ODE.
###   Newton's 2nd Law formalism has been kept (rhs = f(t, u, v)/m)
###   rhs = f - cv - ku
################################################################################################


import matplotlib.pyplot as plt
import numpy as np
from math import *
from sympy import *
import cmath
import sys

init_printing(use_unicode=True)

class SDoF:

    def __init__(self, time_scheme=None, numerical_scheme=None, K=1.0, M=1, C=0.1, f=0.1, u0=1.0, v0=0.0, dt=0.1):

        self.K = lambda u: (u**2 + 1)
        self.Ku = lambda u: self.K(u) * u
        self.C = C
        self.f = f
        self.u0 = u0
        self.v0 = v0
        self.dt = dt
        self.time_scheme = time_scheme
        self.numerical_scheme = numerical_scheme
        self.tend = 20.0
        self.print_scheme()


    def rhs(self, t, u, v):
        f, C, M = symbols('f C M')
        return (f - self.K(u) * u - C * v) / M

    # Function for the u'(t) = v ODE.
    def g(self, v):
        return v


    def euler_disp_based(self):
        # ### euler ###
        # v_n+1 = v_n + dt f(tn, v_n)
        print("##### Euler Disp #####")

        a_n1, a_n, u_n2, u_n1, u_n, u_nm1, u_nm2, u_nm3, v_n1, v_n, v_nm1, v_nm2, t, dt = symbols('a_n1 a_n u_n2 u_n1 u_n u_nm1 u_nm2 u_nm3 v_n1 v_n v_nm1 v_nm2 t dt')
        f, C, M = symbols('f C M')
        du, ru = symbols('du ru')

        v_n = (u_n1 - u_n) / dt
        v_nm1 = ( u_n - u_nm1) / dt
        a_nm1 = ( v_n - v_nm1 ) / dt

        r_u = f - (M * a_nm1 + C * v_nm1 + self.K(u_n) * u_nm1 )
        print("ru = ", r_u)
        
        drudu = diff(r_u, u_n1)
        eq_u = ru + drudu * du
        sol = solve(eq_u, du)
        du = (sol[0])

        print("du = ", du )


    def bdf1_disp_based(self):
        # ### BDF1 ###
        # v_n+1 = v_n + dt f(tn+1, v_n+1)
        print("##### BDF1 Disp #####")

        a_n1, a_n, u_n2, u_n1, u_n, u_nm1, u_nm2, u_nm3, v_n1, v_n, v_nm1, v_nm2, t, dt = symbols('a_n1 a_n u_n2 u_n1 u_n u_nm1 u_nm2 u_nm3 v_n1 v_n v_nm1 v_nm2 t dt')
        f, C, M = symbols('f C M')
        du, ru = symbols('du ru')

        v_n1 = ( u_n1 - u_n) / dt
        v_n = ( u_n - u_nm1) / dt
        a_n1 = ( v_n1 - v_n ) / dt

        if self.numerical_scheme == 'Newton Raphson':
            r_u = f - ( M * a_n1 + C * v_n1 + self.K(u_n1) * u_n1 )

        elif self.numerical_scheme == 'Picard':
            r_u = f - ( M * a_n1 + C * v_n1 + self.K(u_n) * u_n1 )

        print("ru = ", r_u)

        drudu = diff(r_u, u_n1)
        eq_u = ru + drudu * du
        sol = solve(eq_u, du)
        du = (sol[0])

        print("du = ", du )


    def bdf2_disp_based(self):
        # ### BDF2 ###
        # v_n+1 = 4/3 v_n - 1/3 v_n-1 + 2/3 dt f(tn+1, v_n+1)
        print("##### BDF2 Disp #####")
        a_n1, a_n, u_n2, u_n1, u_n, u_nm1, u_nm2, u_nm3, v_n1, v_n, v_nm1, v_nm2, t, dt = symbols('a_n1 a_n u_n2 u_n1 u_n u_nm1 u_nm2 u_nm3 v_n1 v_n v_nm1 v_nm2 t dt')
        f, C, M = symbols('f C M')
        du, ru = symbols('du ru')

        bdf0 =  3 * 0.5/dt
        bdf1 =  -4 * 0.5/dt
        bdf2 =  1 * 0.5/dt

        v_n1 = bdf0 * u_n1 + bdf1 * u_n + bdf2 * u_nm1
        v_n = bdf0 * u_n + bdf1 * u_nm1 + bdf2 * u_nm2
        v_nm1 =  bdf0 * u_nm1 + bdf1 * u_nm2 + bdf2 * u_nm3

        a_n1 = bdf0 * v_n1 + bdf1 * v_n + bdf2 * v_nm1

        if self.numerical_scheme == 'Newton Raphson':
            r_u = f - ( M * a_n1 + C * v_n1 + self.K(u_n1) * u_n1 )

        elif self.numerical_scheme == 'Picard':
            r_u = f - ( M * a_n1 + C * v_n1 + self.K(u_n) * u_n1 )
        
        print("ru = ", r_u)

        drudu = diff(r_u, u_n1)
        eq_u = ru + drudu * du
        sol = solve(eq_u, du)
        du = (sol[0])

        print("du = ", du )


    def euler_vel_based(self):
        # ### euler ###
        # v_n+1 = v_n + dt f(tn, v_n)
        print("##### Euler Vel #####")

        a_n1, a_n, u_n2, u_n1, u_n, u_nm1, u_nm2, u_nm3, v_n1, v_n, v_nm1, v_nm2, t, dt = symbols('a_n1 a_n u_n2 u_n1 u_n u_nm1 u_nm2 u_nm3 v_n1 v_n v_nm1 v_nm2 t dt')
        f, C, M = symbols('f C M')
        dv, rv = symbols('dv rv')

        a_n = (v_n1 - v_n) / dt

        r_v = f - (M * a_n + C * v_n + self.K(u_n) * u_n )
        print("rv = ", r_v)
        
        drvdv = diff(r_v, v_n1)
        eq_v = rv + drvdv * dv
        sol = solve(eq_v, dv)
        dv = (sol[0])

        print("dv = ", dv )


    def bdf1_vel_based(self):
        # ### BDF1 ###
        # v_n+1 = v_n + dt f(tn+1, v_n+1)
        print("##### BDF1 Vel #####")

        a_n1, a_n, u_n2, u_n1, u_n, u_nm1, u_nm2, u_nm3, v_n1, v_n, v_nm1, v_nm2, t, dt = symbols('a_n1 a_n u_n2 u_n1 u_n u_nm1 u_nm2 u_nm3 v_n1 v_n v_nm1 v_nm2 t dt')
        f, C, M = symbols('f C M')
        dv, rv = symbols('dv rv')

        u_n1 = u_n + v_n1 * dt
        a_n1 = (v_n1 - v_n) / dt

        if self.numerical_scheme == 'Newton Raphson':
            r_v = f - ( M * a_n1 + C * v_n1 + self.K(u_n1) * u_n1 )

        elif self.numerical_scheme == 'Picard':
            r_v = f - ( M * a_n1 + C * v_n1 + self.K(u_n) * u_n1 )

        print("rv = ", r_v)

        drvdv = diff(r_v, v_n1)
        eq_v = rv + drvdv * dv
        sol = solve(eq_v, dv)
        dv = (sol[0])

        print("dv = ", dv )


    def bdf2_vel_based(self):
        # ### BDF2 ###
        # v_n+1 = 4/3 v_n - 1/3 v_n-1 + 2/3 dt f(tn+1, v_n+1)
        print("##### BDF2 Disp #####")
        a_n1, a_n, u_n2, u_n1, u_n, u_nm1, u_nm2, u_nm3, v_n1, v_n, v_nm1, v_nm2, t, dt = symbols('a_n1 a_n u_n2 u_n1 u_n u_nm1 u_nm2 u_nm3 v_n1 v_n v_nm1 v_nm2 t dt')
        f, C, M = symbols('f C M')
        dv, rv = symbols('dv rv')

        bdf0 =  3 * 0.5/dt
        bdf1 =  -4 * 0.5/dt
        bdf2 =  1 * 0.5/dt

        u_n1 = 4/3 * u_n - 1/3 * u_nm1 + 2/3 * dt * v_n1
        a_n1 = bdf0 * v_n1 + bdf1 * v_n + bdf2 * v_nm1

        if self.numerical_scheme == 'Newton Raphson':
            r_v = f - ( M * a_n1 + C * v_n1 + self.K(u_n1) * u_n1 )

        elif self.numerical_scheme == 'Picard':
            r_v = f - ( M * a_n1 + C * v_n1 + self.K(u_n) * u_n1 )
        
        print("rv = ", r_v)

        drvdv = diff(r_v, v_n1)
        eq_v = rv + drvdv * dv
        sol = solve(eq_v, dv)
        dv = nsimplify(sol[0])

        print("dv = ", dv )


    def bdf2_vel_based_adaptive(self):
        # ### BDF2 ###
        # v_n+1 = 4/3 v_n - 1/3 v_n-1 + 2/3 dt f(tn+1, v_n+1)
        print("##### BDF2 Vel Adaptive #####")
        a_n1, a_n, u_n2, u_n1, u_n, u_nm1, u_nm2, u_nm3, v_n1, v_n, v_nm1, v_nm2, t, dt = symbols('a_n1 a_n u_n2 u_n1 u_n u_nm1 u_nm2 u_nm3 v_n1 v_n v_nm1 v_nm2 t dt')
        bdf0, bdf1, bdf2 = symbols('bdf0 bdf1 bdf2')
        f, C, M = symbols('f C M')
        dv, rv = symbols('dv rv')

        #v_n1 = bdf0 * u_n1 + bdf1 * u_n + bdf2 * unm1
        u_n1 = (v_n1 - bdf1 * u_n - bdf2 * u_nm1) / bdf0
        a_n1 = bdf0 * v_n1 + bdf1 * v_n + bdf2 * v_nm1

        if self.numerical_scheme == 'Newton Raphson':
            r_v = f - ( M * a_n1 + C * v_n1 + self.K(u_n1) * u_n1 )

        elif self.numerical_scheme == 'Picard':
            r_v = f - ( M * a_n1 + C * v_n1 + self.K(u_n) * u_n1 )
        
        print("rv = ", r_v)

        drvdv = diff(r_v, v_n1)
        eq_v = rv + drvdv * dv
        sol = solve(eq_v, dv)
        dv = nsimplify(sol[0])

        print("dv = ", dv )


    def print_scheme(self):

        if self.time_scheme == 'euler_disp':
            self.euler_disp_based()

        if self.time_scheme == 'bdf1_disp':
            self.bdf1_disp_based()

        if self.time_scheme == 'bdf2_disp':
            self.bdf2_disp_based()
        
        if self.time_scheme == 'euler_vel':
            self.euler_vel_based()

        if self.time_scheme == 'bdf1_vel':
            self.bdf1_vel_based()

        if self.time_scheme == 'bdf2_vel':
            self.bdf2_vel_based()

        if self.time_scheme == 'bdf2_vel_adaptive':
            self.bdf2_vel_based_adaptive()


if __name__ == "__main__":
    # Get command line arguments
    #my_sdof = SDoF('bdf2_vel_adaptive','Newton Raphson')
    my_sdof = SDoF('bdf2_vel_adaptive','Picard')
