"""

This script is an example of: 
1. How to make linac lattice
2. See lattice nodes, how to get quads, BPM markers, correctors
3. How to generate bunch fro known Twiss parameters
4. How to get Twiss parameters of the bunch
5. How to create BPM models as children of BPM marker nodes
6. How to track bunch through the lattice
7. How to generate Transport matrices during the tracking
8. How to see bunch parameters along the tracking

"""

import os
import sys
import math
import random
import time

random.seed(100)

#-------------------------------------------------------------------
#         Let's build lattice from XML input file
#-------------------------------------------------------------------

from orbit.py_linac.linac_parsers import SNS_LinacLatticeFactory

#---- Names of sequences
names = ["MEBT","DTL1",]

#---- create the lattice factory instance
sns_linac_factory = SNS_LinacLatticeFactory()

#---- the XML file name with the structure
xml_file_name = os.environ["HOME"] + "/uspas24-CR/lattice/sns_linac.xml"

#---- make lattice from XML file 
accLattice = sns_linac_factory.getLinacAccLattice(names,xml_file_name)

print ("Linac lattice =",accLattice.getName()," is ready. Length[m] = ",accLattice.getLength())

#---------------------------------------------------------------
#   Nodes, BPM markers, Correctors H & V, quads, Wire Scanners
#---------------------------------------------------------------
from orbit.py_linac.lattice import MarkerLinacNode
from orbit.py_linac.lattice import DCorrectorV,DCorrectorH

nodes = accLattice.getNodes()

#---- dictionary with list of start and end positions of 1st level nodes
node_position_dict = accLattice.getNodePositionsDict()

bpms = []
for node in accLattice.getNodes():
	if(isinstance(node,MarkerLinacNode) and node.getName().find("BPM") >= 0):
		bpms.append(node)
		continue
	for childNode in node.getBodyChildren():
		if(isinstance(childNode,MarkerLinacNode) and childNode.getName().find("BPM") >= 0):
			bpms.append(childNode)
			continue

dcv_nodes = []
for node in accLattice.getNodes():
	if(isinstance(node,DCorrectorV)):
		dcv_nodes.append(node)
		continue
	for childNode in node.getBodyChildren():
		if(isinstance(childNode,DCorrectorV)):
			dcv_nodes.append(childNode)
			continue

quad_nodes = accLattice.getQuads()

#----- accLattice.getNodesForSubstring(substring_is_present,substring_is_not_present)
ws_nodes = accLattice.getNodesForSubstring("WS","drift")

rf_cavs = accLattice.getRF_Cavities()

rf_gaps = accLattice.getRF_Gaps()

#-----------------------------------------------------------------------
#---- Now we add phase aperture nodes which will remove particles 
#---- that are too far from the synchronous particle longitudinally 
#-----------------------------------------------------------------------
#--- Add the new directory to the PYTHONPATH - from the common local packages
sys.path.append('../uspas_pylib/')

from aperture_nodes_lib import addPhaseApertureNodes
addPhaseApertureNodes(accLattice)

#--------------------------------------------
print ("Start Bunch Generation for MEBT")
#--------------------------------------------

from orbit.bunch_generators import TwissContainer
from orbit.bunch_generators import WaterBagDist3D, GaussDist3D, KVDist3D

from sns_linac_bunch_generator import SNS_Linac_BunchGenerator

#------ Twiss X,Y  - (alpha,beta,emitt) in beta in meters, emitt [pi*mm*mrad]
#------ Twiss long - (alpha,beta,emitt) in beta in meters, emitt [pi*m*GeV]
(alphaX,betaX,emittX) = ( -1.9569,  0.1821,  2.8724*1.0e-6)
(alphaY,betaY,emittY) = (  1.7703,  0.1624,  2.8826*1.0e-6)
(alphaZ,betaZ,emittZ) = ( -0.0216,116.0548,  0.0165*1.0e-6)
                                                                      
twissX = TwissContainer(alphaX,betaX,emittX)
twissY = TwissContainer(alphaY,betaY,emittY)
twissZ = TwissContainer(alphaZ,betaZ,emittZ)

bunch_gen = SNS_Linac_BunchGenerator(twissX,twissY,twissZ)

#set the initial kinetic energy in GeV
e_kin_ini = 0.0025
bunch_gen.setKinEnergy(e_kin_ini)

#set the beam peak current in mA
peak_current = 37.0 
bunch_gen.setBeamCurrent(peak_current)

n_particles = 10000
bunch_in = bunch_gen.getBunch(nParticles = n_particles, distributorClass = WaterBagDist3D)
#bunch_in = bunch_gen.getBunch(nParticles = n_particles, distributorClass = GaussDist3D)
#bunch_in = bunch_gen.getBunch(nParticles = n_particles, distributorClass = KVDist3D)
#--------------------------------------------
print("Bunch Generation completed.")
#--------------------------------------------

#--------------------------------------------
#  Let's get Twiss from bunch
#--------------------------------------------
from orbit.core.bunch import Bunch
from orbit.core.bunch import BunchTwissAnalysis

#---- instance of a class for Bunch analysis
twiss_analysis = BunchTwissAnalysis()

twiss_analysis.analyzeBunch(bunch_in)

(alphaX, betaX, emittX) = (twiss_analysis.getTwiss(0)[0], twiss_analysis.getTwiss(0)[1], twiss_analysis.getTwiss(0)[3] * 1.0e6)
(alphaY, betaY, emittY) = (twiss_analysis.getTwiss(1)[0], twiss_analysis.getTwiss(1)[1], twiss_analysis.getTwiss(1)[3] * 1.0e6)
(alphaZ, betaZ, emittZ) = (twiss_analysis.getTwiss(2)[0], twiss_analysis.getTwiss(2)[1], twiss_analysis.getTwiss(2)[3] * 1.0e6)
st  = "(alphaX, betaX, emittX) =   %+7.4f  %7.4f  %7.4f " % (alphaX, betaX, emittX) + "\n"
st += "(alphaY, betaY, emittY) =   %+7.4f  %7.4f  %7.4f " % (alphaY, betaY, emittY) + "\n"
st += "(alphaZ, betaZ, emittZ) =   %+7.4f  %7.4f  %7.4f " % (alphaZ, betaZ, emittZ)
print ("--------------------------------------")
print (st)
print ("--------------------------------------")

#-------------------------------------------------------------
#  Let's add BPM Models to all BPM marker-nodes as child-nodes
#-------------------------------------------------------------
from orbit.lattice import AccNode
from bpm_model_node_lib import ModelBPM

#---- BPM freqiency: MEBT,DTL - 805 MHz, CCL,SCL,HEBT - 402.5MHz
bpm_frequency = 805.0e+6

bpm_model_nodes = []
for bpm in bpms:
	position = bpm.getPosition()
	bpm_model_node = ModelBPM(twiss_analysis, bpm, position, peak_current, bpm_frequency)
	bpm_model_node.setNumberParticles(n_particles)
	bpm.addChildNode(bpm_model_node,AccNode.ENTRANCE)
	bpm_model_nodes.append(bpm_model_node)
	print ("bpm-model=",bpm_model_node.getName()," position [m]= %7.3f "%bpm_model_node.getPosition())

#--------------------------------------------
#   How to track bunch through the lattice
#--------------------------------------------

dcv_nodes[0].setField(0.05)

bunch = Bunch()
bunch_in.copyBunchTo(bunch)

#---- set up design for RF cavities
accLattice.trackDesignBunch(bunch)

#---- really track bunch
accLattice.trackBunch(bunch)

for bpm_model in bpm_model_nodes:
	(x,xp,y,yp,avg_phase,eKin) = bpm_model.getCoordinates()
	st  = "bpm=" + bpm_model.getName()
	st += " x,y [mm] = %+5.2f %+5.2f "%(x,y)
	st += " phase [deg] = %+5.1f "%avg_phase
	print (st)
	
#-------------------------------------------------------------
#  How to generate Transport matrices during the tracking
#-------------------------------------------------------------
from orbit.py_linac.lattice import LinacTrMatricesContrioller

from matrix_lib import printMatrix

#---- let's restore the corrector
dcv_nodes[0].setField(0.0)

quad_index = 0
ws_index = 2

#---- Transport Matrix Controller organizes the new child nodes and calculations 
trMatricesGenerator = LinacTrMatricesContrioller()
lattice_transpMatrxNodes = [quad_nodes[quad_index],ws_nodes[ws_index]]
trMatrixNodes = trMatricesGenerator.addTrMatrxGenNodesAtEntrance(accLattice,lattice_transpMatrxNodes)

#---- The use of Twiss weights makes transport matrices more accurate.
for trMtrxNode in trMatrixNodes:
	#---- setting up to use Twiss weights for transport matrix calculations
	#---- for X,Y,Z directions.
	trMtrxNode.setTwissWeightUse(True,True,True)
	
bunch = Bunch()
bunch_in.copyBunchTo(bunch)

#---- really track bunch
accLattice.trackBunch(bunch)

for trMatrixNode in trMatrixNodes:
	trMtrx = trMatrixNode.getTransportMatrix()
	printMatrix(trMtrx," Transport Matrix ")
print ("----------------------------------------------")

#-------------------------------------------------------------
# How to see bunch parameters along the tracking
#-------------------------------------------------------------
from orbit.lattice import AccActionsContainer

# track through the lattice
paramsDict = {"old_pos": -1.0, "count": 0, "pos_step": 0.1}
actionContainer = AccActionsContainer("Bunch Tracking")

pos_start = 0.0

file_out = open("pyorbit_twiss_sizes_ekin.dat", "w")

s = " Node   position "
s += "   alphaX betaX emittX  normEmittX"
s += "   alphaY betaY emittY  normEmittY"
s += "   alphaZ betaZ emittZ  emittZphiMeV"
s += "   sizeX sizeY sizeZ_deg"
s += "   eKin Nparts "
file_out.write(s + "\n")
print(" N node   position   sizeX  sizeY  sizeZdeg  eKin Nparts ")


def action_entrance(paramsDict):
    node = paramsDict["node"]
    bunch = paramsDict["bunch"]
    pos = paramsDict["path_length"]
    if paramsDict["old_pos"] == pos:
        return
    if paramsDict["old_pos"] + paramsDict["pos_step"] > pos:
        return
    paramsDict["old_pos"] = pos
    paramsDict["count"] += 1
    gamma = bunch.getSyncParticle().gamma()
    beta = bunch.getSyncParticle().beta()
    twiss_analysis.analyzeBunch(bunch)
    x_rms = math.sqrt(twiss_analysis.getTwiss(0)[1] * twiss_analysis.getTwiss(0)[3]) * 1000.0
    y_rms = math.sqrt(twiss_analysis.getTwiss(1)[1] * twiss_analysis.getTwiss(1)[3]) * 1000.0
    z_rms = math.sqrt(twiss_analysis.getTwiss(2)[1] * twiss_analysis.getTwiss(2)[3]) * 1000.0
    z_to_phase_coeff = bunch_gen.getZtoPhaseCoeff(bunch)
    z_rms_deg = z_to_phase_coeff * z_rms / 1000.0
    nParts = bunch.getSizeGlobal()
    (alphaX, betaX, emittX) = (twiss_analysis.getTwiss(0)[0], twiss_analysis.getTwiss(0)[1], twiss_analysis.getTwiss(0)[3] * 1.0e6)
    (alphaY, betaY, emittY) = (twiss_analysis.getTwiss(1)[0], twiss_analysis.getTwiss(1)[1], twiss_analysis.getTwiss(1)[3] * 1.0e6)
    (alphaZ, betaZ, emittZ) = (twiss_analysis.getTwiss(2)[0], twiss_analysis.getTwiss(2)[1], twiss_analysis.getTwiss(2)[3] * 1.0e6)
    norm_emittX = emittX * gamma * beta
    norm_emittY = emittY * gamma * beta
    # ---- phi_de_emittZ will be in [pi*deg*MeV]
    phi_de_emittZ = z_to_phase_coeff * emittZ
    eKin = bunch.getSyncParticle().kinEnergy() * 1.0e3
    s = " %35s  %4.5f " % (node.getName(), pos + pos_start)
    s += "   %6.4f  %6.4f  %6.4f  %6.4f   " % (alphaX, betaX, emittX, norm_emittX)
    s += "   %6.4f  %6.4f  %6.4f  %6.4f   " % (alphaY, betaY, emittY, norm_emittY)
    s += "   %6.4f  %6.4f  %6.4f  %6.4f   " % (alphaZ, betaZ, emittZ, phi_de_emittZ)
    s += "   %5.3f  %5.3f  %5.3f " % (x_rms, y_rms, z_rms_deg)
    s += "  %10.6f   %8d " % (eKin, nParts)
    file_out.write(s + "\n")
    file_out.flush()
    s_prt = " %5d  %35s  %4.5f " % (paramsDict["count"], node.getName(), pos + pos_start)
    s_prt += "  %5.3f  %5.3f   %5.3f " % (x_rms, y_rms, z_rms_deg)
    s_prt += "  %10.6f   %8d " % (eKin, nParts)
    print(s_prt)


def action_exit(paramsDict):
    action_entrance(paramsDict)


actionContainer.addAction(action_entrance, AccActionsContainer.ENTRANCE)
actionContainer.addAction(action_exit, AccActionsContainer.EXIT)

time_start = time.process_time()

bunch = Bunch()
bunch_in.copyBunchTo(bunch)
accLattice.trackBunch(bunch, paramsDict = paramsDict, actionContainer = actionContainer)

time_exec = time.process_time() - time_start
print("time[sec]=", time_exec)

file_out.close()


print ("Stop.")





