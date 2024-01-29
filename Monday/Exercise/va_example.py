# This is an example script using the virtual accelerator.

# Importing epics to use pyepics to talk to Epics
import epics

# Importing time to allow our script to sleep while we wait for changes to be registered.
import time

# Imports to help with plotting.
import numpy as np
from matplotlib import pyplot as plt

# PV names for the cavity we want to change.
cavity_name = "SCL_LLRF:FCM23d"
# PV name for the BPM we want to read.
BPM_name = "SCL_Diag:BPM32"

# Here we grab the initial cavity phase. "CtlPhaseSet" is added to the cavity name to specify the phase.
initial_phase = epics.caget(cavity_name + ":CtlPhaseSet")

# Setup for the scan to make a plot later.
num = 11
cavity_phases = np.linspace(-10 + initial_phase, 10 + initial_phase, num)
bpm_phases = np.zeros(num)

print("Cavity Phase [degrees]    BPM Phase [degrees]")
for i in range(len(cavity_phases)):
    # Set the cavity phase
    epics.caput(cavity_name + ":CtlPhaseSet", cavity_phases[i])

    # Sleep long enough for the cavity to change.
    time.sleep(1.5)

    # Read the arrival phase of the BPM after sleeping long enough for it to update.
    bpm_phases[i] = epics.caget(BPM_name + ":phaseAvg")

    print(cavity_phases[i], bpm_phases[i])

# Return the cavity phase to it's original value.
epics.caput(cavity_name + ":CtlPhaseSet", initial_phase)

# Plot the results.
plt.plot(cavity_phases, bpm_phases, 'o')
plt.xlabel("Cavity Phase [degrees]")
plt.ylabel("BPM Phase [degrees]")
plt.show()
