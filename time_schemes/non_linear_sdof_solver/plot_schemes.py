from itertools import cycle
import matplotlib.pyplot as plt
import sys
plt.rc('font',family='TeX Gyre Termes')
plt.rcParams.update({'font.size': 16})
plt.rc('text', usetex=True)

USE_TWO_VARIABLE_FORMULATOIN = True
USE_ADAPTIVE_TIME_STEP = False  
NUMERICAL_SCHEME = 'Newton Raphson'

if USE_TWO_VARIABLE_FORMULATOIN == True:
    sys.path.append('two_variables')
else:
    sys.path.append('one_variable')

if USE_ADAPTIVE_TIME_STEP == True:
    from adaptive_nonlinear_sdof_solver import SDoF
else:
    from nonlinear_sdof_solver import SDoF

cycol = cycle('bgrcmk')
fig, axes = plt.subplots(2,1,figsize = (16,5))
time_schemes = [ "euler", "bdf1", "bdf2"]

def plot(sdof, time_scheme):
    global axes, cycol

    color = next(cycol)

    t, u, v = sdof.solve(time_scheme)

    axes[0].set_title(r"$Mu''(t) + Cu'(t) + Ku(t) = f(t), u(0) = 1, v(0) = 0$")
    axes[0].set_xlabel("t")
    axes[0].set_ylabel("u(t)")
    axes[0].grid('on')
    axes[0].plot(t, u, c = color)

    axes[1].set_xlabel("t")
    axes[1].set_ylabel("v(t)")
    axes[1].grid('on')
    axes[1].plot(t, v, c = color, label=time_scheme)

K = 1.
M = 1.
C = 0.2

for time_scheme in time_schemes:
    sdof = SDoF(time_scheme, NUMERICAL_SCHEME, K, M, C)
    plot(sdof, time_scheme)
#plt.show()

lgd = axes[1].legend(loc='lower center', bbox_to_anchor=(0.5, -0.65), fancybox=False, ncol=len(time_schemes))
plt.savefig("post_processing_results/two_varaibles_const_dt.png", bbox_extra_artists=(lgd,),bbox_inches='tight')