import glob
import os
import networkx as nx


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

	def __str__(self):
		return "(type:{}, startTime:{}, endTime:{}, length:{}, visited:{}, needArow:{}, fromRank:{}, toRank:{})".format( \
			self.type, self.startTime, self.endTime, self.length, self.visited, self.needArrow, self.fromRank, self.toRank)

	def updateStartTime(self, newStartTime):
		if (self.visited):
			if (newStartTime > self.startTime):
				self.startTime = newStartTime
				self.endTime = self.startTime + self.length
		else:
			self.startTime = newStartTime
			self.endTime = self.startTime + self.length
			self.visited = 1;

		return self.endTime

	def speedup(self, speedup):
		self.length = self.length / speedup
		self.endTime = self.startTime + self.length

		return self.endTime

	def speedupReverse(self, speedup):
		self.length = self.length * speedup
		self.endTime = self.startTime + self.length

		return self.endTime

	def markNotVisited(self):
		self.visited = 0;

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

	def needsArrowOut(self, successor, arrowStartTime, fromRank):
		if ((self.needArrow == "Need_Arrow_Out") and (self.fromRank == fromRank) and (self.type == "MPI_Send_Start")):
			endTime = successor.getEndTime()
			if ((arrowStartTime >= self.startTime) and (arrowStartTime <= endTime)):
				return True

		return False

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

class GraphWrapper:
	def __init__(self):
		self.graph = nx.DiGraph()
		self.ranks = dict()
		self.arrowList = list()

	def add_new_node(self, rank, node, updateEndTime):
		self.graph.add_node(node)

		if rank in self.ranks:
			self.graph.add_edge(self.ranks[rank], node)
			if (updateEndTime == True):
				self.ranks[rank].setEndTime(node.getStartTime())


		self.ranks[rank] = node

	def add_arrow_node_deferred(self, node):
		self.arrowList.append(node)

	#might still be a bug here; be very careful with this function
	def add_all_deferred_arrows(self):
		for arrow in self.arrowList:
			self.graph.add_node(arrow)
			arrowPlaced = False
			for outNode in self.graph.nodes(data=False):
				outSuccessor = self.getSoleSuccessor(outNode)
				if (outNode.needsArrowOut(outSuccessor, arrow.getStartTime(), arrow.getFromRank())):
					outNode.setEndTime(arrow.getStartTime())
					outSuccessor.setStartTime(arrow.getStartTime())
					outSuccessor.setAssociatedRank(arrow.getToRank())
					self.graph.add_edge(outNode, arrow)

					for inNode in self.graph.nodes(data=False):
						inSuccessor = self.getSoleSuccessor(inNode)
						if (inNode.needsArrowIn(inSuccessor, arrow.getEndTime(), arrow.getToRank())):
							inSuccessor.setStartTime(arrow.getEndTime())
							self.graph.add_edge(arrow, inSuccessor)
							arrowPlaced = True
							break

					if (arrowPlaced == True):
						break
			if (arrowPlaced != True):
				print("ERROR!\n")



	def getSoleSuccessor(self, node):
		for successor in self.graph.successors(node):
			if (successor != node):
				return successor

	def printAllNodes(self):
		for node in self.graph.nodes(data=False):
			print(node)

	def propagate(self, node, newEndTime):
		for successor in self.graph.successors(node):
			self.propagate(successor, successor.updateStartTime(newEndTime))

	def backPropagate(self, targetType, speedupFactor):
		for node in self.graph.nodes(data=False):
			if (node.isTargetType(targetType)):
				newEndTime = node.speedupReverse(speedupFactor)
				self.propagate(node, newEndTime)
				self.markAllNodesUnvisited()

	def backPropagateHW(self, speedupFactor, rank):
		for node in self.graph.nodes(data=False):
			if (node.isTargetType("Worker")):
				if (node.getFromRank() == rank):
					newEndTime = node.speedup(speedupFactor)
					self.propagate(node, newEndTime)
					self.markAllNodesUnvisited()
				
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




class Primitive:
	def __init__(self, startTime, endTime, fromRank, toRank, category):
		self.startTime = startTime
		self.endTime = endTime
		self.fromRank = fromRank
		self.toRank = toRank
		self.category = category
		self.startNode = 0
		self.endNode = 0

	def toFile(self):
		return "Primitive[ TimeBBox({0},{1}) Category={2} ({0}, {3}) ({1}, {4}) ]\n".format(self.startTime, self.endTime, self.category, self.fromRank, self.toRank)

	def spawnNodes(self, G, categoryDict):
		categoryType = categoryDict[self.category]

		if (categoryType == "MPI_Send"):

			startSendNode = GraphNode("MPI_Send_Start", self.startTime, -1, "Need_Arrow_Out", self.fromRank, self.toRank)
			endSendNode = GraphNode("MPI_Send_End", -1, self.endTime, "No", self.fromRank, self.toRank)
			workNode = GraphNode("Worker", self.endTime, -1, "No", self.fromRank, self.toRank)

			self.startNode = startSendNode
			self.endNode = endSendNode

			G.add_new_node(self.fromRank, startSendNode, True)
			G.add_new_node(self.fromRank, endSendNode, False)
			G.add_new_node(self.fromRank, workNode, True)


		elif (categoryType == "MPI_Recv"):

			startRecvNode = GraphNode("MPI_Recv_Start", self.startTime, self.startTime, "Need_Arrow_In", self.fromRank, self.toRank)
			endRecvNode = GraphNode("MPI_Recv_End", -1, self.endTime, "No", self.fromRank, self.toRank)
			workNode = GraphNode("Worker", self.endTime, -1, "No", self.fromRank, self.toRank)

			self.startNode = startRecvNode
			self.endNode = endRecvNode

			G.add_new_node(self.fromRank, startRecvNode, True)
			G.add_new_node(self.fromRank, endRecvNode, True)
			G.add_new_node(self.fromRank, workNode, True)

		elif (categoryType == "message"):

			arrowNode = GraphNode("Arrow", self.startTime, self.endTime, "No", self.fromRank, self.toRank)

			self.startNode = arrowNode
			self.endNode = 0

			G.add_arrow_node_deferred(arrowNode)

		elif (categoryType == "MPE_Comm_finalize"):

			finalNode = GraphNode("Final", self.startTime, self.endTime, "No", self.fromRank, self.toRank)

			self.startNode = finalNode
			self.endNode = 0

			G.add_new_node(self.fromRank, finalNode, True)

		else:

			otherNode = GraphNode("Other", self.startTime, self.endTime, "No", self.fromRank, self.toRank)
			workNode = GraphNode("Worker", self.endTime, -1, "No", self.fromRank, self.toRank)

			self.startNode = otherNode
			self.endNode = 0

			G.add_new_node(self.fromRank, otherNode, True)
			G.add_new_node(self.fromRank, workNode, True)

	def updateTimesFromSpawnedNodes(self):
		self.startTime = self.startNode.getStartTime()
		if (self.endNode != 0):
			self.endTime = self.endNode.getEndTime()
		else:
			self.endTime = self.startNode.getEndTime()


def processLogLine(line, categoryDict, primitiveList, newTextLogFile, G):
	if line.startswith("Category"):
		categoryDict[int(line.split("index=")[1].split("name")[0])] = line.split("name=")[1].split("topo")[0].strip()
		newTextLogFile.write(line)

	if line.startswith("Primitive"):

		category = int(line.split("Category=")[1].split(" ", 1)[0])
		startTime = float(line.split("(", 1)[1].split(",", 1)[0])
		endTime = float(line.split(",", 1)[1].split(")", 1)[0])

		fromRank = int(line.split("Category=")[1].split(",", 1)[1].split(")", 1)[0])

		if (startTime != endTime):
			toRank = int(line.split("Category=")[1].split(",", 2)[2].split(")", 2)[0])
		else:
			toRank = fromRank



		newPrimitive = Primitive(startTime, endTime, fromRank, toRank, category)
		newPrimitive.spawnNodes(G, categoryDict)
		primitiveList.append(newPrimitive)

def addPrimitvesToFile(primitiveList, newTextLogFile):
	newTextLogFile.write("\n")
	for primitive in primitiveList:
		primitive.updateTimesFromSpawnedNodes()
		newTextLogFile.write(primitive.toFile())

def processTextLog(oldTextlogFile, newTextLogFile, categoryDict, primitiveList, G):
	for line in oldTextlogFile:
		processLogLine(line, categoryDict, primitiveList, newTextLogFile, G)

	G.add_all_deferred_arrows()


def main(HWRankAccelerationFactors, NWAccelerationFactors):

	graph = GraphWrapper()

	oldTextlogFile = open("./Unknown.textlog", "r")
	newTextLogFile = open("./new.textlog", "w+")


	categoryDict = dict()
	primitiveList = list()

	processTextLog(oldTextlogFile, newTextLogFile, categoryDict, primitiveList, graph)

	for i in range(len(HWRankAccelerationFactors)):
		if (HWRankAccelerationFactors[i] != 1):
			graph.backPropagateHW(HWRankAccelerationFactors[i], i)

	for i in range(len(NWAccelerationFactors)):
		for j in range(len(NWAccelerationFactors[i])):
			if (NWAccelerationFactors[i][j] != 1):
				graph.backPropagateNetwork(NWAccelerationFactors[i][j], i, j)

	#targetType1 = "MPI_Send_End"
	#targetType2 = "Worker"
	#speedupFactor = 0.7

	#graph.printAllNodes()
	#graph.backPropagate(targetType1, speedupFactor)
	#graph.backPropagate(targetType2, speedupFactor)
	addPrimitvesToFile(primitiveList, newTextLogFile)





if __name__ == '__main__':
	emptyList1 = list()
	emptyList2 = list()
	main(emptyList1, emptyList2)

