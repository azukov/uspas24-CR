"""
This script will track the bunch through the SNS Linac.

The tracking will be performed for the design parameters of the lattice
and for a case with shifted phases of all SCL cavities. 

"""

import os
import sys
import math
import random
import time

from orbit.py_linac.linac_parsers import SNS_LinacLatticeFactory

from orbit.bunch_generators import TwissContainer
from orbit.bunch_generators import WaterBagDist3D, GaussDist3D, KVDist3D

from orbit.core.bunch import Bunch, BunchTwissAnalysis

from orbit.lattice import AccNode, AccActionsContainer
from orbit.py_linac.lattice import MarkerLinacNode

from orbit.utils import phaseNearTargetPhaseDeg

from uspas_pylib.bpm_model_node_lib import ModelBPM

from uspas_pylib.aperture_nodes_lib import addPhaseApertureNodes

from uspas_pylib.sns_linac_bunch_generator import SNS_Linac_BunchGenerator

random.seed(100)

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

n_particles = 1000

#--------------------------------------------
#---- Let's make the lattice
#--------------------------------------------

names = ["SCLMed","SCLHigh","HEBT1"]
#---- create the factory instance
sns_linac_factory = SNS_LinacLatticeFactory()

#---- the XML file name with the structure
xml_file_name = os.environ["HOME"] + "/uspas24-CR/lattice/sns_linac.xml"

#---- make lattice from XML file 
accLattice = sns_linac_factory.getLinacAccLattice(names,xml_file_name)

#---- dictionary with the start and end positions of 1st level nodes
node_position_dict = accLattice.getNodePositionsDict()

#---- list of RF cavities and markers (BPMs, Wire Scanners etc.) 
rf_cavs = accLattice.getRF_Cavities()
marker_nodes = accLattice.getNodesOfClass(MarkerLinacNode)

print("Linac lattice is ready. L=", accLattice.getLength())

#---- instance of a class for Bunch analysis
twiss_analysis = BunchTwissAnalysis()

#---- Let's create BPM-Model nodes
bpm_model_nodes = []
cav_1st_position = rf_cavs[0].getPosition()
for marker_node in marker_nodes:
	if(marker_node.getName().find("BPM") >= 0):
		bpm = marker_node
		position = (node_position_dict[bpm][0] + node_position_dict[bpm][1])/2.
		if(position < cav_1st_position): continue
		bpm_model_node = ModelBPM(twiss_analysis, bpm, position, peak_current, bpm_frequency)
		bpm_model_node.setNumberParticles(n_particles)
		bpm.addChildNode(bpm_model_node,AccNode.ENTRANCE)
		bpm_model_nodes.append(bpm_model_node)
		#print ("debug bpm-model=",bpm_model_node.getName()," position=",bpm_model_node.getPosition())

#---- Now we add phase aperture nodes which will remove particles 
#---- that are too far from the synchronous particle longitudinally 
addPhaseApertureNodes(accLattice)

#--------------------------------------------
print ("Start Bunch Generation.")

#------ Twiss X,Y  - (alpha,beta,emitt) in beta in meters, emitt [pi*mm*mrad]
#------ Twiss long - (alpha,beta,emitt) in beta in meters, emitt [pi*m*GeV]
(alphaX,betaX,emittX) = ( -1.3264,  2.0412, 1.0379*1.0e-6)
(alphaY,betaY,emittY) = (  1.8856,  9.9807, 0.3921*1.0e-6)
(alphaZ,betaZ,emittZ) = (  0.1040, 13.0192, 0.3812*1.0e-6)
                                                                      
twissX = TwissContainer(alphaX,betaX,emittX)
twissY = TwissContainer(alphaY,betaY,emittY)
twissZ = TwissContainer(alphaZ,betaZ,emittZ)

bunch_gen = SNS_Linac_BunchGenerator(twissX,twissY,twissZ)

#set the initial kinetic energy in GeV
bunch_gen.setKinEnergy(e_kin_ini)

#set the beam peak current in mA
bunch_gen.setBeamCurrent(peak_current)

bunch_in = bunch_gen.getBunch(nParticles = n_particles, distributorClass = WaterBagDist3D)
#bunch_in.dumpBunch("bunch_at_scl_entrance.dat")

print("Bunch Generation completed.")

#-----------------------------------------------------------
#---- Now we perform tracking the synchronous particle 
#---- for the design lattice settings to remember
#---- arraival time at each RF cavity
#-----------------------------------------------------------

#---- we will keep bunch_in and always start with its copy
bunch = Bunch()
bunch_in.copyBunchTo(bunch)

#set up design for RF cavities
accLattice.trackDesignBunch(bunch)

print ("Design tracking has been completed.")


bunch = Bunch()
bunch_in.copyBunchTo(bunch)
accLattice.trackBunch(bunch)

print ("Tracking the bunch through the design lattice has been completed.")

#-------------------------------------
#---- let's remember BPMs' phases
#-------------------------------------
bpm_phases_init_arr = []
print ("----------- Design BPM Phases ---------")
print (" BPM    pos[m]   Phase[deg] ")
for bpm_model in bpm_model_nodes:
	bpm_phase = bpm_model.getPhase()
	bpm_phases_init_arr.append(bpm_phase)
	st = " %22s  %7.3f   %+6.1f "%(bpm_model.getName(),bpm_model.getPosition(),bpm_phase)
	print (st)
print ("---------------------------------------")


#-------------------------------------------
#---- Now we change all RF phases by +1 deg
#-------------------------------------------
rf_phase_shift = -5.0
for rf_cav in rf_cavs:
	cav_phase = rf_cav.getPhase()
	cav_phase_new = cav_phase + rf_phase_shift*math.pi/180.
	rf_cav.setPhase(cav_phase_new)
	#print ("debug cav=",rf_cav.getName()," cav_phase=",cav_phase*180./math.pi)

#---- track bunch with new RF phases
bunch = Bunch()
bunch_in.copyBunchTo(bunch)
accLattice.trackDesignBunch(bunch)

accLattice.trackBunch(bunch)

bpm_phases_delta_arr = []
bpm_pos_arr = []
print ("----------- After Phase Shift---------")
print (" BPM    pos[m]   Delta[deg] ")
for i, bpm_model in enumerate(bpm_model_nodes):
	bpm_phase = bpm_model.getPhase()
	delta = bpm_phase-bpm_phases_init_arr[i]
	if delta < -180:
		delta += 360
	elif delta > 180:
		delta -= 360

	bpm_phases_delta_arr.append(delta)
	bpm_pos_arr.append(bpm_model.getPosition())
	st = " %22s  %7.3f   %+6.4f "%(bpm_model.getName(),bpm_model.getPosition(), delta)
	print (st)
print ("---------------------------------------")

import matplotlib.pyplot as plt

plt.plot(bpm_pos_arr, bpm_phases_delta_arr)
plt.show()

sys.exit(0)
