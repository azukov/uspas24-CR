"""
This script is the start of the home work where you
have to close 3-kickers bump using DCV01, DCV04, 
and DCV05 correctors in MEBT.

It shows how to create PV names and communicate with 
the Virtual Accelerator.

>virtual_accelerator --debug  --sequences MEBT

"""

import sys
import math
import time

from epics import pv as pv_channel

#-------------------------------------------------------------------
#              START of the SCRIPT
#-------------------------------------------------------------------

#---- DCV01, DCV04, DCV05, DCV10, DCV11, DCV14  
dcv_ind_arr = [1,4,5,10,11,14]
dcv_field_pv_arr = []
for ind in dcv_ind_arr:
	dcv_field_pv_arr.append(pv_channel.PV("MEBT_Mag:PS_DCV"+"%02d"%ind+":B_Set"))

#---- put 0. [T] field in all DCV
for pv in dcv_field_pv_arr:
	pv.put(0.)

#---- set DCV01 t0 field 0.05 [T]
dcv01_field = 0.05
dcv_field_pv_arr[0].put(dcv01_field)

#---- give the accelerator time to put beam through MEBT
time.sleep(2.0)	

#---- BPM01, BPM04, BPM05, BPM10, and BPM11
bpm_ind_arr = [1,4,5,10,11,14]
bpm_ver_pos_pv_arr = []
for ind in bpm_ind_arr:
	bpm_ver_pos_pv_arr.append(pv_channel.PV("MEBT_Diag:BPM"+"%02d"%ind+":yAvg"))

#-------------------------------------------------
#---- Let's print BPM signals before bump closing
#-------------------------------------------------
print ("======= BPMs before Closing =====")
for bpm_pv in bpm_ver_pos_pv_arr:
	print ("BPM PV=",bpm_pv.pvname," y_avg[mm] = %+12.5g "%bpm_pv.get())
print ("=================================")
