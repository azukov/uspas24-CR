"""
This script will use Virtual Accelerator to scan phase of the 1st SCL cavity
recording the BPM11 phase. It will write the data into a file for future
analysis.

>virtual_accelerator --debug  --sequences SCLMed --bunch bunch_at_scl_entrance.dat --particle_number 1000 --refresh_rate 5
"""

import os
import sys
import math
import random
import time

from epics import pv as pv_channel

from orbit.utils  import phaseNearTargetPhaseDeg

from orbit.py_linac.linac_parsers import SNS_LinacLatticeFactory
from orbit.py_linac.lattice import MarkerLinacNode

from uspas_pylib.harmonic_data_fitting_lib import fitCosineFunc

#-------------------------------------------------------------------
#              START of the SCRIPT
#-------------------------------------------------------------------

names = ["SCLMed",]
#---- create the factory instance
sns_linac_factory = SNS_LinacLatticeFactory()

#---- the XML file name with the structure
xml_file_name = os.environ["HOME"] + "/uspas24-CR/lattice/sns_linac.xml"

#---- make lattice from XML file 
accLattice = sns_linac_factory.getLinacAccLattice(names,xml_file_name)

cavs = accLattice.getRF_Cavities()
cav = cavs[0]
bpms = accLattice.getNodesForSubstring(":BPM","drift")
bpm = bpms[-1]
print ("=======================================")
print ("cav=",cav.getName()," pos= %8.3f"%cav.getPosition())
print ("BPM=",bpm.getName()," pos= %8.3f"%bpm.getPosition())
print ("=======================================")

"""
for cav in cavs:
	print ("cav=",cav.getName()," pos=",cav.getPosition())
print ("=======================================")
for bpm in bpms:
	print ("bpm=",bpm.getName()," pos=",bpm.getPosition())
"""

bpm_amp_pv = pv_channel.PV("SCL_Diag:BPM11:amplitudeAvg")
bpm_phase_pv = pv_channel.PV("SCL_Diag:BPM11:phaseAvg")

print ("bpm=",bpm.getName()," amplitude= %+8.5f"%bpm_amp_pv.get())
print ("bpm=",bpm.getName()," phas[deg]= %+8.2f"%bpm_phase_pv.get())

bpm_production_amp = bpm_amp_pv.get()

def cavNameFromIndex(ind):
	letter_arr = ["a","b","c"]
	cryo_mod_ind, letter_ind = divmod(ind,3)
	cav_name = "SCL_LLRF:FCM" + "%02d"%(cryo_mod_ind+1)+letter_arr[letter_ind]
	return cav_name

for ind,cav in enumerate(cavs[1:]):
	cav_amp_pv_name = cavNameFromIndex(ind+1)+":CtlAmpSet"
	cav_amp_pv = pv_channel.PV(cav_amp_pv_name)
	cav_amp_pv.put(0.)
	#print ("cav pv name=",cav_amp_pv_name)
	
cav_amp_pv = pv_channel.PV( cavNameFromIndex(0)+":CtlAmpSet")
cav_phase_pv = pv_channel.PV(cavNameFromIndex(0)+":CtlPhaseSet")
print ("cav=",cav.getName()," amplitude= %+8.5f"%cav_amp_pv.get())
print ("cav=",cav.getName()," phase[deg]= %+8.2f"%cav_phase_pv.get())

print ("=======================================")

#------------------------------------
# To be continued
#------------------------------------

