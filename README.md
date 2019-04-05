# MPI_FPGA_SIMULATOR

Setup:

1. Run 'sudo apt-get install mpich' to install MPI.
2. Download MPE from the following link and follow instructions for installation: https://www.mcs.anl.gov/research/projects/perfvis/download/index.htm
3. Run 'sudo apt-get install python3' to install python3
4. Run 'sudo apt-get install python3-pyqt5' to install PyQT5. Required for the GUI.
5. run python 2_simulator_gui.py to start the program.


More information about the simulator implementation can be found in the Final Report Document.

How To Use Simulator:

Starter_GUI:

The starter GUI lets the user indicate how many network types (ex: Ethernet connection, FPGA to FPGA bus connection) exist in the hardware topology. The number ranks indicates number of MPI ranks in the program to be simulated. Alternatively, can open from a previously saved config file.

Main GUI:

In the top left box, the user can select the directory that contains the source files of the program to be simulated. They can also enter the command line arguments that would be used to run the program.

The user can then enter network acceleration factors (how much faster or slower the network in the hardware topology would be) and which hardware ranks those network factors correspond to. Hardware acceleration factors corresponding to the specific MPI rank in software can also be entered.

Click Start Simulation to begin the simulation workflow. It will compile the source code using MPE, and run it through our backend and then visualized.

Click on Save to Config to save the current state of the GUI to a config file. It will be saved to the same directory as the simulator.

Reading the simulator graphical output:

The final simulation output uses MPE jumpshot. Explanation of how to use it can be found here: https://www.mcs.anl.gov/research/projects/perfvis/software/viewers/index.htm


