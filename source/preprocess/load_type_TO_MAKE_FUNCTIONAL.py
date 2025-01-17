import numpy as np


# TODO: update script so that it works with current code structure


# =========================dynamic analysis ==========================
# generating signals in time domain
def load_type(force_dynamic, array_time, num_of_levels, freq=10, force_static=1):
    """
    Choose from "signalSin", "signalRand", "signalConst", "signalSuperposed" or 
    for free vibration choose "signalNone" 
    """

    if (force_dynamic == "signalNone"):
        # constant signal with given amplitude = 10
        force_dynamic = np.zeros([num_of_levels, len(array_time)])

    elif (force_dynamic == "signalSin"):
        # sine with given amplitude = 1 and frequency
        amplSin = force_static[:, np.newaxis]
        force_dynamic = amplSin * np.sin(2*np.pi*freq * array_time)

    elif (force_dynamic == "signalRand"):
        # normal random signal with given mean m = 0 and standard dev sd = 0.25 ->
        # check out difference compared to unifrnd - uniform random distribution
        force_dynamic = np.random.normal(
            0, 0.25, [num_of_levels, len(array_time)])

    elif (force_dynamic == "signalConst"):
        # constant signal with given amplitude = 10
        amplConst = force_static[:, np.newaxis]
        force_dynamic = amplConst * np.ones(len(array_time))

    elif (force_dynamic == "signalSuperposed"):
        # superposing the signals
        amplConst = force_static[:, np.newaxis]
        signalConst = amplConst * np.ones(len(array_time))

        amplSin = 1 * np.ones([num_of_levels, 1])
        signalSin = amplSin * np.sin(2*np.pi*freq * array_time)

        signalRand = np.random.normal(
            0, 0.25, [num_of_levels, len(array_time)])

        # superposition weighting
        coefSignal1 = 1
        coefSignal2 = 0.25
        coefSignal3 = 0.25

        force_dynamic = coefSignal1 * signalConst + \
            coefSignal2 * signalSin + coefSignal3 * signalRand

    else:
        err_msg = "The requested dynamic load \"" + force_dynamic
        err_msg += "\" is not available \n"
        err_msg += "Choose one of: \"signalConst\", \"signalSin\", \"signalRand\", \"signalSuperposed\", \"signalNone\""
        raise Exception(err_msg)

    return force_dynamic
