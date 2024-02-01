"""
This script is to help you with the orbit correction project. It sets up the PyORBIT part of the problem.
You will need the results from the virtual accelerator part for this to work.
"""
import os

from orbit.py_linac.linac_parsers import SNS_LinacLatticeFactory

from orbit.core.bunch import Bunch, BunchTwissAnalysis

from orbit.lattice import AccActionsContainer

from orbit.py_linac.lattice_modifications import Add_quad_apertures_to_lattice
from orbit.py_linac.lattice_modifications import Add_rfgap_apertures_to_lattice

# The sequences we want need for this problem.
names = ["MEBT", "DTL1", "DTL2", "DTL3", "DTL4", "DTL5", "DTL6", "CCL1", "CCL2", "CCL3", "CCL4"]
# The XML file with the structure
xml_file_name = os.environ["HOME"] + "/uspas24-CR/lattice/sns_linac.xml"

# create the factory instance and create the SNS Linac lattice.
sns_linac_factory = SNS_LinacLatticeFactory()
accLattice = sns_linac_factory.getLinacAccLattice(names, xml_file_name)

print("Linac lattice is ready. L=", accLattice.getLength())

# Add apertures to lattice nodes.
aprtNodes = Add_quad_apertures_to_lattice(accLattice)
aprtNodes = Add_rfgap_apertures_to_lattice(accLattice, aprtNodes)

# This adds the kick from the problem statement to the DTL correctors.
DTL_correctors = {'DTL_Mag:DCH618': 0.005, 'DTL_Mag:DCV621': -0.004}
for name, field in DTL_correctors.items():
    DTL_cor = accLattice.getNodeForName(name)
    DTL_cor.setField(field)

# This dictionary connects the model name of the correctors to their nodes so you can change their fields.
# Ex: CCL_correctors[pyorbit_name].setField(new_field)
CCL_correctors = {}
quads = accLattice.getQuads()
for quad in quads:
    children = quad.getAllChildren()
    for child_node in children:
        name = child_node.getName()
        if 'DC' in name and 'CCL' in name:
            CCL_correctors[name] = child_node

# Load bunch from file. This bunch is designed to enter the MEBT.
bunch_file = os.environ["HOME"] + "/uspas24-CR/lattice/MEBT_in.dat"
bunch_in = Bunch()
bunch_in.readBunch(bunch_file)

# Decrease the number of particles in the bunch (to speed up simulation and match the virtual accelerator.)
num_part = 1000 # The number of particles you are tracking.
bunch_orig_num = bunch_in.getSizeGlobal()
for n in range(bunch_orig_num):
    if n + 1 > num_part:
        bunch_in.deleteParticleFast(n)
bunch_in.compress()

print("Bunch Generation completed.")

# Set up the lattice cavities
accLattice.trackDesignBunch(bunch_in)

print("Design tracking completed.")

# Define twiss analysis in case you want to use its functions for your calculations.
twiss_analysis = BunchTwissAnalysis()

# Here is a parameter dictionary in case you want to use it.
my_params = {}


# Here is the action function for you to fill in with your calculations.
def action_entrance(paramsDict):
    node = paramsDict["node"]
    bunch = paramsDict["bunch"]
    pos = paramsDict["path_length"]


def action_exit(paramsDict):
    action_entrance(paramsDict)


# Defining our action container to implement your action while tracking.
actionContainer = AccActionsContainer("Measure Beam Position along Lattice")
# Add you action to the entrance and exit of each node.
actionContainer.addAction(action_entrance, AccActionsContainer.ENTRANCE)
actionContainer.addAction(action_exit, AccActionsContainer.EXIT)

# Track your bunch, passing your actions and parameters.
accLattice.trackBunch(bunch_in, paramsDict=my_params, actionContainer=actionContainer)
print("Done tracking!")
