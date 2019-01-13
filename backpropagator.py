import glob
import os
import networkx as nx

#################################################################################################
#                                                                                     
# Class representing the nodes of the graph which describe the input textlog
#
# Class Attributes:
#
#	type: the type of the node (worker, message, etc...)
#	starTime: the start time of the node; depends on the end times of ancestor nodes
#	endTime: the end time of the node
#	length: end time - start time
#	visited: used when doing backpropagation; this flag denotes whether the node has been visited
#	needArrow: used when initially populating the graph; a node that "needs an arrow" means that 
#			   a message node points at it
#	fromRank: in the case of a "message" node, this represents where the message originated from; 
#			  otherwise, this is simply the rank of the node
#	toRank: in the case of a "message" node, this represents where the message goes to; 
#			  otherwise, this is simply the rank of the node
#	associatedRank: In the case of MPI_Send_End, we need to keep track of the rank that is receiving the message
# 
##################################################################################################
class GraphNode:
	def __init__(self, nodeType, startTime, endTime, needArrow, fromRank, toRank):
		self.type = nodeType
		self.startTime = startTime
		self.endTime = endTime
		self.length = endTime - startTime;
		self.visited = 0;
		self.needArrow = needArrow; 
		self.fromRank = fromRank
		self.toRank = toRank
		self.associatedRank = -1
		self.arrowArrivalReferenceNode = -1;
		self.ancestorEndTimes = [-1, -1]

	#method for printing a node
	def __str__(self):
		return "(type:{}, startTime:{}, endTime:{}, length:{}, visited:{}, needArow:{}, fromRank:{}, toRank:{})".format( \
			self.type, self.startTime, self.endTime, self.length, self.visited, self.needArrow, self.fromRank, self.toRank)

	#update the start time when backpropogating
	def updateStartTime(self, newStartTime, index):
		#if (self.visited):
			#if (newStartTime > self.startTime):
				#self.startTime = newStartTime
				#self.endTime = self.startTime + self.length
		#else:
		if (self.type != "MPI_Recv_End"):
			self.startTime = newStartTime
			self.endTime = self.startTime + self.length
			#if (self.type == "Arrow"):
				#if (self.endTime < self.arrowArrivalReferenceNode.getStartTime()):
					#self.endTime = self.arrowArrivalReferenceNode.getStartTime()
					#self.length = self.endTime - self.startTime
		else:
			self.ancestorEndTimes[index] = newStartTime
			self.startTime = max(self.ancestorEndTimes[0], self.ancestorEndTimes[1])
			self.endTime = self.startTime + self.length
			#self.visited = 1;

		return self.endTime

	def speedup(self, speedup):
		self.length = self.length / speedup
		self.endTime = self.startTime + self.length

		if (self.type == "Arrow"):
			if (self.endTime < self.arrowArrivalReferenceNode.getStartTime()):
				self.endTime = self.arrowArrivalReferenceNode.getStartTime()
				self.length = self.endTime - self.startTime

		return self.endTime

	def speedupReverse(self, speedup):
		self.length = self.length * speedup
		self.endTime = self.startTime + self.length

		return self.endTime

	def markNotVisited(self):
		self.visited = 0;

	def getType(self):
		return self.type

	def getEndTime(self):
		return self.endTime

	def getStartTime(self):
		return self.startTime

	def setEndTime(self, endTime):
		if (self.endTime == -1):
			self.endTime = endTime
			self.length = self.endTime - self.startTime

	def setStartTime(self, startTime):
		if (self.startTime == -1):
			self.startTime = startTime
			self.length = self.endTime - self.startTime

	#basically check to see if the given "message" should start from this node
	def needsArrowOut(self, successor, arrowStartTime, fromRank):
		if ((self.needArrow == "Need_Arrow_Out") and (self.fromRank == fromRank) and (self.type == "MPI_Send_Start")):
			endTime = successor.getEndTime()
			if ((arrowStartTime >= self.startTime) and (arrowStartTime <= endTime)):
				return True

		return False

	#basically check to see if the given "message" should end at this node
	def needsArrowIn(self, successor, arrowEndTime, toRank):
		if ((self.needArrow == "Need_Arrow_In") and (self.fromRank == toRank) and (self.type == "MPI_Recv_Start")):
			endTime = successor.getEndTime()
			if ((arrowEndTime >= self.startTime) and (arrowEndTime <= endTime)):
				return True

		return False

	def isTargetType(self, targetType):
		if (self.type == targetType):
			return True
		else:
			return False

	def getFromRank(self):
		return self.fromRank

	def getToRank(self):
		return self.toRank

	def getAssociatedRank(self):
		return self.associatedRank

	def setAssociatedRank(self, rank):
		self.associatedRank = rank

	def setArrowEarliestArrivalRef(self, node):
		self.arrowArrivalReferenceNode = node

	def getArrowEarliestArrivalRef(self):
		return self.arrowArrivalReferenceNode

	def setAncestorEndTimes(self, endTime, index):
		self.ancestorEndTimes[index] = endTime

#################################################################################################
#                                                                                     
# Class representing the graph that represents the textlog
#
# Class Attributes:
#
#	graph: the graph
#	ranks: a dictionary that contains the final node of each rank currently in the graph;
#		   used when populating the grab
#	arrowList: a list of all message nodes; these nodes get inserted into the graph last. and have to
#			   to be stored temporarily in this structure
# 
##################################################################################################
class GraphWrapper:
	def __init__(self):
		self.graph = nx.DiGraph()
		self.ranks = dict()
		self.arrowList = list()

	#for every non message node, insert it directly after the last node of the same rank
	def add_new_node(self, rank, node, updateEndTime):
		self.graph.add_node(node)

		if rank in self.ranks:
			self.graph.add_edge(self.ranks[rank], node)
			if (updateEndTime == True):
				self.ranks[rank].setEndTime(node.getStartTime())


		self.ranks[rank] = node

	def add_arrow_node_deferred(self, node):
		self.arrowList.append(node)

	#place all the "message" nodes after all other nodes have already been placed
	def add_all_deferred_arrows(self):
		for arrow in self.arrowList:
			self.graph.add_node(arrow)
			arrowPlaced = False

			#iterate through all nodes to see which one the "message" node should start from
			for outNode in self.graph.nodes(data=False):
				outSuccessor = self.getSoleSuccessor(outNode)

				#check to see if this message should originate from this node
				if (outNode.needsArrowOut(outSuccessor, arrow.getStartTime(), arrow.getFromRank())):
					outNode.setEndTime(arrow.getStartTime())
					outSuccessor.setStartTime(arrow.getStartTime())
					outSuccessor.setAssociatedRank(arrow.getToRank())
					self.graph.add_edge(outNode, arrow)

					#iterate through all nodes to see which one the "message" node should end at
					for inNode in self.graph.nodes(data=False):
						inSuccessor = self.getSoleSuccessor(inNode)

						#check to see if this message should point at this node
						if (inNode.needsArrowIn(inSuccessor, arrow.getEndTime(), arrow.getToRank())):
							inSuccessor.setStartTime(arrow.getEndTime())
							inSuccessor.setAncestorEndTimes(arrow.getEndTime(), 1)
							arrow.setArrowEarliestArrivalRef(inNode)
							self.graph.add_edge(arrow, inSuccessor)
							arrowPlaced = True
							break

					if (arrowPlaced == True):
						break

			#if we have not placed the message node, something went wrong
			if (arrowPlaced != True):
				print("ERROR!\n")



	def getSoleSuccessor(self, node):
		for successor in self.graph.successors(node):
			if (successor != node):
				return successor

	def printAllNodes(self):
		for node in self.graph.nodes(data=False):
			print(node)

	#propogate the startTime change to the successor
	def propagate(self, node, newEndTime):
		for successor in self.graph.successors(node):
			index = 0
			if (node.getType() == "Arrow"):
				index = 1
				#self.propagate(node.getArrowEarliestArrivalRef(), node.getArrowEarliestArrivalRef().updateStartTime(newEndTime, index))
			#else:
			self.propagate(successor, successor.updateStartTime(newEndTime, index))

	#if the node matches the target type, change its length, and propogate the change
	def backPropagate(self, targetType, speedupFactor):
		for node in self.graph.nodes(data=False):
			if (node.isTargetType(targetType)):
				newEndTime = node.speedupReverse(speedupFactor)
				self.propagate(node, newEndTime)
				self.markAllNodesUnvisited()

	#if the node matches the target type and rank, change its length, and propogate the change
	#Used for doing backpropagation on HW rank speedup
	def backPropagateHW(self, speedupFactor, rank):
		for node in self.graph.nodes(data=False):
			if (node.isTargetType("Worker")):
				if (node.getFromRank() == rank):
					newEndTime = node.speedup(speedupFactor)
					self.propagate(node, newEndTime)
					self.markAllNodesUnvisited()
				
	#used for back propogation for network speedup
	#need to do it for two types of nodes: messages, and the second half of MPI_Send
	#for the latter, we need to know its associated rank (ie which rank does the MPI_send send to)
	def backPropagateNetwork(self, speedupFactor, fromRank, toRank):
		for node in self.graph.nodes(data=False):
			if (node.isTargetType("Arrow")):
				if ((node.getFromRank() == fromRank) and (node.getToRank() == toRank)):
					newEndTime = node.speedup(speedupFactor)
					self.propagate(node, newEndTime)
					self.markAllNodesUnvisited()
			elif (node.isTargetType("MPI_Send_End")):
				if ((node.getFromRank() == fromRank) and (node.getAssociatedRank() == toRank)):
					newEndTime = node.speedup(speedupFactor)
					self.propagate(node, newEndTime)
					self.markAllNodesUnvisited()


	def markAllNodesUnvisited(self):
		for node in self.graph:
			node.markNotVisited()



#################################################################################################
#                                                                                     
# Class representing primitive types in the textlog file. One or more nodes are spwaned from primitives
#
# Class Attributes:
#
#	startTime: the start time of the primitive
#	endTime: the end time of the primitive (could be same as start time)
#	fromRank: in the case of a "message", this represents where the message originated from; 
#			  otherwise, this is simply the rank of the primitive
#	toRank: in the case of a "message", this represents where the message goes to; 
#			  otherwise, this is simply the rank of the primitive
#	category: type of primitive (message, mpi_send, mpi_recv)
#	startnode: a primitive corresponds to one or more nodes in the graph. The startNode represents the first of
#			   these nodes. It is necessary to keep track of it to update the start time of the primitive
#	startnode: a primitive corresponds to one or more nodes in the graph. The endNode represents the last of
#			   these nodes. It is necessary to keep track of it to update the end time of the primitive
# 
##################################################################################################
class Primitive:
	def __init__(self, startTime, endTime, fromRank, toRank, category):
		self.startTime = startTime
		self.endTime = endTime
		self.fromRank = fromRank
		self.toRank = toRank
		self.category = category
		self.startNode = 0
		self.endNode = 0

	#write primitive back to file
	def toFile(self):
		return "Primitive[ TimeBBox({0},{1}) Category={2} ({0}, {3}) ({1}, {4}) ]\n".format(self.startTime, self.endTime, self.category, self.fromRank, self.toRank)

	#spawn the corresponding graph nodes of this primitive, and keep track of the first and last nodes
	#Every primitive except for messages are followed by worker nodes: these nodes represent the work being done by the rank
	def spawnNodes(self, G, categoryDict):
		categoryType = categoryDict[self.category]

		#spawn the following nodes, they are connected to each other linearly:
		# MPI_Send_Start --> MPI_Send_End --> Worker
		#MPI_Send has to be split into two halves, the first half represents all of MPI_Send before the message is sent out
		if (categoryType == "MPI_Send"):

			#the end time of MPI_Send_Start and the start time of MPI_Send_End is determined by when the message arrives at MPI_Send_End
			#so we put placeholder values of -1 for the times that we do not know
			startSendNode = GraphNode("MPI_Send_Start", self.startTime, -1, "Need_Arrow_Out", self.fromRank, self.toRank)
			endSendNode = GraphNode("MPI_Send_End", -1, self.endTime, "No", self.fromRank, self.toRank)
			workNode = GraphNode("Worker", self.endTime, -1, "No", self.fromRank, self.toRank)

			self.startNode = startSendNode
			self.endNode = endSendNode

			#add nodes to the graph
			G.add_new_node(self.fromRank, startSendNode, True)
			G.add_new_node(self.fromRank, endSendNode, False)
			G.add_new_node(self.fromRank, workNode, True)


		#spawn the following nodes, they are connected to each other linearly:
		# MPI_Recv_Start --> MPI_Recv_End --> Worker
		#MPI_Recv has to be split into two halves, the first half represents all of MPI_Recv before the message is recieved
		elif (categoryType == "MPI_Recv"):

			#the end time of MPI_Recv_Start and the start time of MPI_Recv_End is determined by when the message arrives at MPI_Recv_End
			#so we put placeholder values of -1 for the times that we do not know
			startRecvNode = GraphNode("MPI_Recv_Start", self.startTime, self.startTime, "Need_Arrow_In", self.fromRank, self.toRank)
			endRecvNode = GraphNode("MPI_Recv_End", -1, self.endTime, "No", self.fromRank, self.toRank)
			endRecvNode.setAncestorEndTimes(startRecvNode.getEndTime(), 0)
			endRecvNode.setArrowEarliestArrivalRef(startRecvNode)
			workNode = GraphNode("Worker", self.endTime, -1, "No", self.fromRank, self.toRank)

			self.startNode = startRecvNode
			self.endNode = endRecvNode

			#add nodes to the graph
			G.add_new_node(self.fromRank, startRecvNode, True)
			G.add_new_node(self.fromRank, endRecvNode, True)
			G.add_new_node(self.fromRank, workNode, True)

		#messages have to be handled at the very end, so we defer them until later
		elif (categoryType == "message"):

			arrowNode = GraphNode("Arrow", self.startTime, self.endTime, "No", self.fromRank, self.toRank)

			self.startNode = arrowNode
			self.endNode = 0

			G.add_arrow_node_deferred(arrowNode)

		elif (categoryType == "MPE_Comm_finalize"):

			finalNode = GraphNode("Final", self.startTime, self.endTime, "No", self.fromRank, self.toRank)

			self.startNode = finalNode
			self.endNode = 0

			#add nodes to the graph
			G.add_new_node(self.fromRank, finalNode, True)

		else:

			otherNode = GraphNode("Other", self.startTime, self.endTime, "No", self.fromRank, self.toRank)
			workNode = GraphNode("Worker", self.endTime, -1, "No", self.fromRank, self.toRank)

			self.startNode = otherNode
			self.endNode = 0

			#add nodes to the graph
			G.add_new_node(self.fromRank, otherNode, True)
			G.add_new_node(self.fromRank, workNode, True)

	#basically after all backpropogation is done, use the start and end nodes for this primitive to update its start and end times
	def updateTimesFromSpawnedNodes(self):
		self.startTime = self.startNode.getStartTime()
		if (self.endNode != 0):
			self.endTime = self.endNode.getEndTime()
		else:
			self.endTime = self.startNode.getEndTime()


#process a line of the textlog
def processLogLine(line, categoryDict, primitiveList, newTextLogFile, G):
	if line.startswith("Category"):
		#get the category IDs and what category they correspond to
		categoryDict[int(line.split("index=")[1].split("name")[0])] = line.split("name=")[1].split("topo")[0].strip()
		newTextLogFile.write(line)

	if line.startswith("Primitive"):

		category = int(line.split("Category=")[1].split(" ", 1)[0])
		startTime = float(line.split("(", 1)[1].split(",", 1)[0])
		endTime = float(line.split(",", 1)[1].split(")", 1)[0])

		#its possible for messages to travel backwards in time for some reason
		#thowever the above method of extracting start time and end time doesnt work in case of time travelling messages
		#this fix ensures the start times and end times are always correct for messages
		if (categoryDict[category] == "message"):
			checkStartTime = float(line.split("Category=")[1].split("(", 1)[1].split(",", 1)[0])
			checkEndTime = float(line.split("Category=")[1].split(")", 1)[1].split("(", 1)[1].split(",", 1)[0])

			if (checkStartTime > checkEndTime):
				temp = startTime
				startTime = endTime
				endTime = temp



		fromRank = int(line.split("Category=")[1].split(",", 1)[1].split(")", 1)[0])

		if (startTime != endTime):
			toRank = int(line.split("Category=")[1].split(",", 2)[2].split(")", 2)[0])
		else:
			toRank = fromRank


		#create a new primitive object, spawn nodes from it, and add them to the graph
		#keep track of primitives in a primitive list
		newPrimitive = Primitive(startTime, endTime, fromRank, toRank, category)
		newPrimitive.spawnNodes(G, categoryDict)
		primitiveList.append(newPrimitive)

#add all updated primitives to the new textlog file
def addPrimitvesToFile(primitiveList, newTextLogFile):
	newTextLogFile.write("\n")
	for primitive in primitiveList:
		primitive.updateTimesFromSpawnedNodes()
		newTextLogFile.write(primitive.toFile())

def processTextLog(oldTextlogFile, newTextLogFile, categoryDict, primitiveList, G):
	for line in oldTextlogFile:
		processLogLine(line, categoryDict, primitiveList, newTextLogFile, G)

	#all message nodes that have been deffered are now finally added to the graph
	G.add_all_deferred_arrows()


def main(HWRankAccelerationFactors, NWAccelerationFactors):

	graph = GraphWrapper()

	oldTextlogFile = open("./Unknown.textlog", "r")
	newTextLogFile = open("./new.textlog", "w+")


	categoryDict = dict()
	primitiveList = list()

	processTextLog(oldTextlogFile, newTextLogFile, categoryDict, primitiveList, graph)

	#parse the arguments that have been passed in and see if we need to do any backpropogation
	for i in range(len(HWRankAccelerationFactors)):
		if (HWRankAccelerationFactors[i] != 1):
			graph.backPropagateHW(HWRankAccelerationFactors[i], i)

	for i in range(len(NWAccelerationFactors)):
		for j in range(len(NWAccelerationFactors[i])):
			if (NWAccelerationFactors[i][j] != 1):
				graph.backPropagateNetwork(NWAccelerationFactors[i][j], i, j)

	#targetType1 = "MPI_Send_End"
	#targetType2 = "Arrow"
	#speedupFactor = 0.7

	#graph.printAllNodes()
	#graph.backPropagate(targetType1, speedupFactor)
	#graph.backPropagate(targetType2, speedupFactor)
	#graph.backPropagateNetwork(2, 0, 1)
	#graph.backPropagateHW(2, 0)
	#graph.backPropagateHW(2, 1)
	addPrimitvesToFile(primitiveList, newTextLogFile)

	newTextLogFile.close()
	oldTextlogFile.close()





if __name__ == '__main__':
	emptyList1 = list()
	emptyList2 = list()
	main(emptyList1, emptyList2)

