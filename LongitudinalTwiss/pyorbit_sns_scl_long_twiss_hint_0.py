"""
Using the phases of BPMs we will calculate the amplitude of the cavity, and
then we will use a simplified model "this cavity + drift" to calculate the 
longitudinal Twiss parameters at the entrance of the cavity.
"""

import sys
import math
import random
import time

import numpy
import matplotlib.pyplot as plt

from orbit.py_linac.linac_parsers import SNS_LinacLatticeFactory

from orbit.bunch_generators import TwissContainer
from orbit.bunch_generators import WaterBagDist3D, GaussDist3D, KVDist3D

from orbit.core.bunch import Bunch
from orbit.core.bunch import BunchTwissAnalysis

from orbit.lattice import AccLattice, AccNode, AccActionsContainer

from orbit.py_linac.lattice import MarkerLinacNode

from orbit.py_linac.lattice import LinacTrMatricesContrioller

from orbit.core.orbit_utils import Matrix
from orbit.core.orbit_utils import PhaseVector

from orbit.utils import phaseNearTargetPhaseDeg

from uspas_pylib.sns_linac_bunch_generator import SNS_Linac_BunchGenerator
from uspas_pylib.wire_scanner_node_lib import WS_AccNode

from uspas_pylib.matrix_lib import printMatrix
from uspas_pylib.matrix_lib import printVector
from uspas_pylib.matrix_lib import makePhaseVector
from uspas_pylib.matrix_lib import getCovarianceMatrix
from uspas_pylib.matrix_lib import getCovarianceMatrixWithWeights
from uspas_pylib.matrix_lib import getBeamCorrelations
from uspas_pylib.matrix_lib import getBeamCorrelationsWithWeights
from uspas_pylib.matrix_lib import getErrorWeghtMatrix
from uspas_pylib.matrix_lib import getLongitudinalDriftMatrix2x2
from uspas_pylib.matrix_lib import getLongitudinalRfCavityMatrix2x2

from uspas_pylib.bpm_model_node_lib import ModelBPM

from uspas_pylib.aperture_nodes_lib import addPhaseApertureNodes

from uspas_pylib.harmonic_data_fitting_lib import fitCosineFunc

def getTransportMatrix(qE0TL,rf_frequency,beta,rf_phase,Ldrift,mass):
	"""
	Returns PyORBIT transport matrix for (z_new,dE_new)^T = M * (z,dE)^T
	for "Thin_RF_Gap-drift" lattice.
	qE0TL - amplitude of the RF gap (thin RF cavity) in GeV
	rf_frequency - RF frequency in Hz
	beta - relativistic beta
	rf_phase - RF phase [deg] in deltaE = qE0TL*cos(rf_phase) 
	Ldrift - drift length in m
	mass - mass of the particle
	quadMatrixGenerator could be getQuadMatrix2x2 or getThinQuadMatrix2x2
	"""
	rf_mtr = getLongitudinalRfCavityMatrix2x2(qE0TL,rf_frequency,beta,rf_phase)
	drift_mtr = getLongitudinalDriftMatrix2x2(Ldrift,beta,mass)
	matr = drift_mtr.mult(rf_mtr)
	return matr

def getLSQ_Matrix(qE0TL,rf_frequency,eKin_arr,rf_phase_arr,Ldrift,mass):
	"""
	Creates the LSQ matrix from the 1st lines of transport matrix.
	Matrix defines the system of equations:
	RMS^2[ind] = mtrx[ind][0]*<z^2> + mtrx[ind][1]*<z*dE> +  mtrx[ind][2]*<dE^2> 
	where ind = 0...(len(results_arr)-1)
	<z^2> , <z*dE>, <dE^2> - unknown correlations we want to find. 
	"""
	n_row = len(rf_phase_arr)
	mtrx = Matrix(n_row,3)
	for ind in range(n_row):
		rf_phase = rf_phase_arr[ind]
		eKin = eKin_arr[ind]
		momentum = math.sqrt((eKin + mass)**2 - mass**2)
		beta = momentum/(eKin + mass)
		transport_matrix = getTransportMatrix(qE0TL,rf_frequency,beta,rf_phase,Ldrift,mass)
		m1 = transport_matrix.get(0,0)
		m2 = transport_matrix.get(0,1)
		mtrx.set(ind,0,m1**2)
		mtrx.set(ind,1,2*m1*m2)
		mtrx.set(ind,2,m2**2)
	return mtrx

def getRMS_BPM_Z_2_Vector(bpm_amp_arr,eKin_arr,bpm_frequency,mass):
	"""
	Returns PyORBIT PhaseVector with RMS^2 longitudinal sizes in [m] at BPM 
	calculated from the BPMs' amplitudes for different phases of RF cavity.
	bpm_amp_arr = [bpm_amp0,bpm_amp1, ...] where bpm_amp = bpm_amp_epics/bpm_amp_epics_max
	eKin_arr = [eKin0,eKin1, ...] - kinetic energy in GeV
	bpm_frequency - BPM electronics frequency in Hz
	mass - mass of the particle in GeV
	"""
	v_light = 2.99792458e+8  # in [m/sec]
	n_row = len(bpm_amp_arr)
	rms2_vector = PhaseVector(n_row)
	for ind, bpm_amp in enumerate(bpm_amp_arr):
		rms2 = 0.
		if(bpm_amp >= 1.0): return rms2
		eKin = eKin_arr[ind]
		momentum = math.sqrt((eKin + mass)**2 - mass**2)
		beta = momentum/(eKin + mass)
		#---- bpm phase rms in radians
		rms2_phase = -2*math.log(bpm_amp)
		coeff_phase2_to_z2 = 1./(2*math.pi*bpm_frequency/(beta*v_light))**2
		rms2 = coeff_phase2_to_z2*rms2_phase
		rms2_vector.set(ind,rms2)
	return rms2_vector

#-------------------------------------------------------------------
#              START of the SCRIPT
#-------------------------------------------------------------------

#-----Parameters at the entrance of SCL ---------------
# transverse emittances are unnormalized and in pi*mm*mrad
# longitudinal emittance is in pi*eV*sec
e_kin_ini = 0.1856 # in [GeV]
mass = 0.939294    # in [GeV]
gamma = (mass + e_kin_ini)/mass
beta = math.sqrt(gamma*gamma - 1.0)/gamma
print ("relat. gamma=",gamma)
print ("relat.  beta=",beta)
peak_current = 38. # in mA
#---- RF cavities and BPMs frequencies in Hz
rf_frequency = 805.0e+6
bpm_frequency = 402.5e+6
v_light = 2.99792458e+8  # in [m/sec]


#---- cav_phase_arr = [cav_phase0,cav_phase1, ...]
cav_phase_arr = []
#---- bpm_phase_arr = [wrapped_bpm_phase0,wrapped_bpm_phase1, ...]
bpm_phase_arr = []
#---- bpm_amp_arr = [bpm_amp0,bpm_amp1, ...]
bpm_amp_arr = []

#----------------------------------------------------------
# Read the file with Virtual Accelerator phase scan data
#----------------------------------------------------------
???

#plt.scatter(cav_phase_arr, bpm_phase_arr)
#plt.show()

#plt.plot(cav_phase_arr,bpm_amp_arr)
#plt.show()

#---- results of cos-fitting (use fitCosineFunc(cav_phase_arr,bpm_phase_arr))
#---- bpm_phase_amp - bpm phases +- spread
#---- cav_phase_offset = phase_offset + 180.
???

#---- results after fitting cav_phase_fit_arr is the same as cav_phase_arr
#---- bpm_phase_err_arr - list of (bpm_phase - bpm_fitted_phase) 
(cav_phase_fit_arr,bpm_phase_fit_arr,bpm_phase_err_arr) = scorer.getFittedArrays()

#plt.scatter(cav_phase_arr, bpm_phase_arr)
#plt.plot(cav_phase_fit_arr,bpm_phase_fit_arr)
#plt.show()

#plt.plot(cav_phase_fit_arr,bpm_phase_err_arr)
#plt.show()

bpm_position = ???
rf_cav_position = ???
Ldrift = bpm_position - rf_cav_position

#---- get qE0TL in GeV
???

print (" cav qE0TL [MeV] = %8.3f "%(qE0TL*1000.))

#---- Using qE0TL and initial energy at 1st cavity entrance calculate the energy 
#---- for each cavity phase.
#---- eKin_arr = [eKin0, eKin1,  ...] in MeV
eKin_arr = []
???
	
#---------------------------------------------------
# Let's analyze the initial longitudinal Twiss
# using the "thin_RF_cavity - drift model" matrix
# approach
#----------------------------------------------------

#---- rf_phase_arr are translation real cavity's phases to the matrix model
rf_phase_arr = []
for cav_phase in cav_phase_arr:
	rf_phase = cav_phase + cav_phase_offset
	rf_phase_arr.append(rf_phase)

lsq_matrix = getLSQ_Matrix(qE0TL,rf_frequency,eKin_arr,rf_phase_arr,Ldrift,mass)
	
#--------------------------------------------
# To be continued
#--------------------------------------------

