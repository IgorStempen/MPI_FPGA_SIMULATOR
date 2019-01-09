import configparser
import glob
import os
from os import listdir
from os.path import isfile, join
import backpropagator

def startWorkflow(directory, input_params, network_connections, hardware_nodes):
	pwd = os.getcwd()
	if not os.path.exists('build'):
	    os.mkdir('build')
	    
	os.system('chmod +rwx build')
	saveParameters(network_connections, hardware_nodes, 'default.cfg')

	onlyfiles = [f for f in listdir(directory) if isfile(join(directory, f))]

	compile_command = 'mpecc -mpilog -o executable '

	for file in onlyfiles:
		compile_command = compile_command + directory+'/'+file + ' '

	os.chdir('build')
	os.system(compile_command)
	print(compile_command)

	run_command = 'mpirun -n ' + str(len(hardware_nodes)) + ' executable ' + input_params

	print(run_command)
	os.system(run_command)

	os.system('/usr/local/bin/clog2TOslog2 Unknown.clog2')
	os.system('/home/stempeni/mpi_fpga_simulator/MPE/mpe2-2.4.9b/src/slog2sdk/bin/slog2print Unknown.slog2 > Unknown.textlog')

	#Create the input to the back propagator from user input
	network_factors = [[] for i in range(0,len(hardware_nodes))]
	print(network_factors)
	for factor in network_factors:
		for i in range(0,len(hardware_nodes)):
			factor.append(1)
	print(network_factors)

	for connection in network_connections:
		network_factors[connection[0]][connection[1]] = connection[2]
	print(network_factors)

	backpropagator.main(hardware_nodes, network_factors)

	calls = ['/usr/local/bin/textlogTOslog2 new.textlog','jumpshot new.textlog.slog2']

	for call in calls:
		os.system(call)

	#cleanup
	onlyfiles = [f for f in listdir(os.getcwd()) if isfile(join(os.getcwd(), f))]
	print(onlyfiles)
	for file in onlyfiles:
		os.remove(file)
	os.chdir(pwd)
	os.rmdir('build')

def saveParameters(network_connections, hardware_nodes, filename):
	if filename == '':
		filename = 'default.cfg'

	parser = configparser.ConfigParser(allow_no_value=True)

	for i in range(0, len(network_connections)):
		parser["network_connection_"+str(i)] = {}
		parser["network_connection_"+str(i)]["source"] = str(network_connections[i][0])
		parser["network_connection_"+str(i)]["destination"] = str(network_connections[i][1])
		parser["network_connection_"+str(i)]["acceleration_factor"] = str(network_connections[i][2])
		parser["network_connection_"+str(i)]["name"] = network_connections[i][3]

	parser["hardware_nodes"] = {}
	for j in range(0, len(hardware_nodes)):
		parser["hardware_nodes"]["node_acceleration_factor_"+str(j)] = str(hardware_nodes[j])

	parser.write(open(filename, "w"))
	os.system('chmod +rwx '+filename)

def loadParameters(filename):
	if filename == '':
		filename = 'default.cfg'

	network_connections = []
	hardware_nodes = []

	if os.path.isfile(filename):
		parser = configparser.ConfigParser(allow_no_value=True)
		parser.read(filename)

		for section in parser.sections():
			if section != "hardware_nodes":
				entry = []
				for i in range(len(parser.options(section))):
					if i != len(parser.options(section)) - 1:
						entry.append(float(parser[section][parser.options(section)[i]]))
					else:
						entry.append(parser[section][parser.options(section)[i]])
				network_connections.append(entry)
			else:
				for i in range(len(parser.options(section))):
					hardware_nodes.append(float(parser[section][parser.options(section)[i]]))

	else:
		print(fileName + " does not exist.")
		exit()

	return network_connections, hardware_nodes

def main():
	values = [[1,2,7,"ye"],[2,3,7,"ye"],[3,4,7,"ye"]]
	values2 = [1,2,3,4,5]
	# saveParameters(values,values2,"test1.cfg")
	

	# values3, values4 = loadParameters("test1.cfg")
	# print(values3)
	# print(values4)
	#print(loadParameters(1,"test1.cfg"))
	startWorkflow('/home/buencons/Documents/Platform_Parameter_Resolver/test/', 'dog dog dog', values, values2)

if __name__ == '__main__':
	main()

