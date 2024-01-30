"""
  Example of cos-function fitting using PyORBIT optimization package.
"""

import os
import sys
import math
import random
import time

from orbit.utils  import phaseNearTargetPhaseDeg

from orbit.utils.fitting import Solver
from orbit.utils.fitting import Scorer
from orbit.utils.fitting import SolveStopperFactory
from orbit.utils.fitting import ScoreboardActionListener
from orbit.utils.fitting import VariableProxy
from orbit.utils.fitting import TrialPoint

from orbit.utils.fitting import SimplexSearchAlgorithm

#-------------------------------------------------------------------
#              START of the SCRIPT
#-------------------------------------------------------------------

#--------------------------------------------
#---- Let's create cos-like data
def function(x):
	"""
	y = Amp*cos(phase + phase_offset) + avg_val
	Parameters:
	phase_offset = -20
	amp = 15
	avg_val = -18.
	"""
	phase = (math.pi/180.)*x
	amp = 15.0
	avg_val = -18.
	phase_offset = -20.0*(math.pi/180.)
	y = amp*math.cos(phase + phase_offset) + avg_val
	return y

x_arr = [1.0*x for x in range(-180,+180,17)]
y_arr = [function(x) for x in x_arr]
	
#--------------------------------------------
#---- Let's define initial estimator.
#---- Estimator is not part of PyORBIT package.
#---- It is just create reasonable initial guess.
#--------------------------------------------
def getCosineParamsEstimation(x_arr,y_arr):
	"""
	It returns estimation for phase offset and amplitude for A*cos(phase - 180. + offset) + avg_val.
	because BPM phase minimum is a maximal acceleration.
	"""
	y_max = max(y_arr)
	y_min = min(y_arr)
	y_max_ind = y_arr.index(y_max)
	y_min_ind = y_arr.index(y_min)
	#---- estimations
	amp = (y_max - y_min)/2.
	phase_offset = - phaseNearTargetPhaseDeg(x_arr[y_max_ind],0.)
	avg_val = sum(y_arr)/len(y_arr)
	return (phase_offset,amp,avg_val)
	
(phase_offset,amp,avg_val) = getCosineParamsEstimation(x_arr,y_arr)
print ("(phase_offset,amp,avg_val) = ",(phase_offset,amp,avg_val))

#-------------------------------------------------------------
#---- Let's define initial trial point - PyORBIT class
#---- TrialPoint has VariableProxy inside
#------------------------------------------------------------
phase_abs_step = 5.0 # in degrees
amp_relative_step = 0.05

trialPoint = TrialPoint()

variableProxy = VariableProxy("phase_offset", phase_offset , phase_abs_step)
trialPoint.addVariableProxy(variableProxy)

variableProxy = VariableProxy("A", amp , amp_relative_step*amp)
trialPoint.addVariableProxy(variableProxy)

variableProxy = VariableProxy("avg_val", avg_val , phase_abs_step)
trialPoint.addVariableProxy(variableProxy)

param_arr = trialPoint.getVariableProxyValuesArr()
print ("From TrialPoint (phase_offset,amp,avg_val) = ",param_arr)

#-------------------------------------------------------------
#---- Let's define scorer - it should return value estimating 
#---- difference between data and fit 
#------------------------------------------------------------

class CosFittingScorer(Scorer):
	"""
	The Scorer implementation for A0+A1*cos(phase + offset1)
	"""
	def __init__(self,x_arr,y_arr):
		self.x_arr = x_arr
		self.y_arr = y_arr
		
	def getScore(self,trialPoint):
		"""
		Implementation of getScore method for Scorer class.
		Calculates sum of squares of differences between goal and fitted values
		"""
		[phase_offset,amp,avg_val] = trialPoint.getVariableProxyValuesArr()
		phase_offset_rad = phase_offset*(math.pi/180.)
		diff2 = 0.
		for ind, x in enumerate(self.x_arr):
			y = self.y_arr[ind]
			phase = (math.pi/180.)*x
			y_fit = amp*math.cos(phase + phase_offset_rad) + avg_val
			diff2 += (y_fit - y)**2
		diff2 /= len(self.x_arr)
		return diff2
		
#------------------------------------------------------------
#---- Now we perform fiiting
#------------------------------------------------------------

#---- Instance of Scorer class 
scorer = CosFittingScorer(x_arr,y_arr)

#---- After this point nothing specific for cos-like function

#---- Search algorithm from PyORBIT native package
searchAlgorithm = SimplexSearchAlgorithm()

maxIter = 50
solverStopper = SolveStopperFactory.maxIterationStopper(maxIter)
#max_time = 0.01
#solverStopper = SolveStopperFactory.maxTimeStopper(max_time)

solver = Solver()
solver.setAlgorithm(searchAlgorithm)
solver.setStopper(solverStopper)

class BestScoreListener(ScoreboardActionListener):
	def __init__(self):
		ScoreboardActionListener.__init__(self)
		
	def performAction(self,solver):
		scoreBoard = solver.getScoreboard()
		iteration = scoreBoard.getIteration()
		trialPoint = scoreBoard.getBestTrialPoint()
		print ("============= iter=",scoreBoard.getIteration()," best score=",scoreBoard.getBestScore())
		print (trialPoint.textDesciption())

#---- if we want to see the progress of fitting 
solver.getScoreboard().addBestScoreListener(BestScoreListener())

#----- Fitting process itself
solver.solve(scorer,trialPoint)	

#---- the fitting process ended, now we see results
print ("========== fitting time =",solver.getScoreboard().getRunTime())

bestScore = solver.getScoreboard().getBestScore()
iteration = solver.getScoreboard().getIteration()
print ("best score=",bestScore," iteration=",iteration)

trialPoint = solver.getScoreboard().getBestTrialPoint()
print (trialPoint.textDesciption())

print ("=======The PyORBIT fitting example END==========")

#------------------------------------------------
#---- Already packaged cos-like fitting
#------------------------------------------------

#--- Add the new directory to the PYTHONPATH - from the common local packages
sys.path.append('../uspas_pylib/')

#---- import fitCosineFunc for fitting
from harmonic_data_fitting_lib import fitCosineFunc

((amp,phase_offset,avg_val),scorer) = fitCosineFunc(x_arr,y_arr,show_progress = False)
print ("(phase_offset,amp,avg_val) = ",(phase_offset,amp,avg_val))

print ("=======Stop.==========")
sys.exit(0)


