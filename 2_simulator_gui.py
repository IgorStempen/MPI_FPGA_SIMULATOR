
import sys

from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QRadioButton, QScrollBar, QSizePolicy,
        QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
        QVBoxLayout, QWidget, QDoubleSpinBox, QFileDialog, QAction, QScrollArea, QFrame, QSpacerItem)

from PyQt5 import QtCore

import workflowScript

#######################################################################################
#                                                                                     #
#                              IMPORTANT CLASS ATTRIBUTES                             #
#                              __________________________                             #
#                                                                                     #
# 1. programFile[0] //Global variable that holds string of path to executable         #
#                   //of program to be simulated                                      #
#                                                                                     #
# 2. InputParameters.text() //Global variable that holds str of executable parameters #
#                                                                                     #
# 3. networkValueBoxList //List of network value boxes that hold network acceleration #
#                        //factors. Accessed by networkValueBoxList[n].value()        #
#                                                                                     #
# 4. hwValueBoxList //List of hardware value boxes that hold hardware Acceleration    #
#                    //factors. Accessed by hwValueBoxList[n].value()                 #
#                                                                                     #
# 5. SavedConfigFileName.text() //class attribute that holds config filename          #
#######################################################################################
class MPI_Simulator_GUI(QDialog):

    #CONSTRUCTOR FOR MAIN GUI WINDOW
    def __init__(self, numNetworkFactors, numHWFactors, network_connections=None, hardware_nodes=None):
        super().__init__()

        if network_connections is not None:
            self.network_connections = network_connections
        if hardware_nodes is not None:
            self.hardware_nodes = hardware_nodes

        self.numNetworkFactors = numNetworkFactors
        self.numHWFactors = numHWFactors
        

        self.originalPalette = QApplication.palette()

        styleComboBox = QComboBox()
        styleComboBox.addItems(QStyleFactory.keys())

        styleLabel = QLabel("&Style:")
        styleLabel.setBuddy(styleComboBox)

        self.useStylePaletteCheckBox = QCheckBox("&Use style's standard palette")
        self.useStylePaletteCheckBox.setChecked(True)

        disableWidgetsCheckBox = QCheckBox("&Disable widgets")

        #Call functions that create GUI elements in each quadrant of the main window
        self.createTopLeftGroupBox()
        self.createTopRightGroupBox()

        if network_connections is not None:
            self.createConfigBottomLeftGroupBox(numNetworkFactors)
        else:
            self.createBottomLeftGroupBox(numNetworkFactors)

        if hardware_nodes is not None:
            self.createConfigBottomRightGroupBox(numHWFactors)
        else:
            self.createBottomRightGroupBox(numHWFactors)

        styleComboBox.activated[str].connect(self.changeStyle)
        self.useStylePaletteCheckBox.toggled.connect(self.changePalette)
        disableWidgetsCheckBox.toggled.connect(self.topLeftGroupBox.setDisabled)
        disableWidgetsCheckBox.toggled.connect(self.topRightGroupBox.setDisabled)
        disableWidgetsCheckBox.toggled.connect(self.bottomLeftGroupBox.setDisabled)
        disableWidgetsCheckBox.toggled.connect(self.bottomRightGroupBox.setDisabled)

        topLayout = QHBoxLayout()
        topLayout.addWidget(styleLabel)
        topLayout.addWidget(styleComboBox)
        topLayout.addStretch(1)
        topLayout.addWidget(self.useStylePaletteCheckBox)
        topLayout.addWidget(disableWidgetsCheckBox)

        mainLayout = QGridLayout()
        mainLayout.addLayout(topLayout, 0, 0, 1, 2)
        mainLayout.addWidget(self.topLeftGroupBox, 1, 0)
        mainLayout.addWidget(self.topRightGroupBox, 1, 1)
        mainLayout.addWidget(self.scrollNetworkWindow, 2, 0)
        mainLayout.addWidget(self.scrollhwWindow, 2, 1)
        mainLayout.setRowStretch(1, 1)
        mainLayout.setRowStretch(2, 1)
        mainLayout.setColumnStretch(0, 1)
        mainLayout.setColumnStretch(1, 1)
        self.setLayout(mainLayout)

        self.setWindowTitle("MPI Performance Co-Simulator")
        self.changeStyle('Fusion')

    def changeStyle(self, styleName):
        QApplication.setStyle(QStyleFactory.create(styleName))
        self.changePalette()

    def changePalette(self):
        if (self.useStylePaletteCheckBox.isChecked()):
            QApplication.setPalette(QApplication.style().standardPalette())
        else:
            QApplication.setPalette(self.originalPalette)

    ############################################################################
    ##                                                                        ##
    ##                  FUNCTIONS LINKED TO GUI EVENTS                        ##
    ##                                                                        ##
    ############################################################################
    def selectProgramFile(self):
        self.programFile = QFileDialog.getExistingDirectory(self, 'Select Directory')
        print(self.programFile)
        
        global filePath
        filePath.setText(self.programFile)

        #debug print messages
        # print(programFile[0])
        # print(InputParameters.text())

    def startSimulation(self):
        print("Executing MPE workflow")

        self.toConfigNetworkParamList = []

        print("SAVING NETWORK ACCEL FACTORS")

        for i in range(0, self.numNetworkFactors):
            entry = []

            entry.append(self.netSourceBoxList[i].value())
            #print(self.netSourceBoxList[i].value())
            entry.append(self.netDestBoxList[i].value())
            #print(self.netDestBoxList[i].value())
            entry.append(self.networkValueBoxList[i].value())
            #print(self.networkValueBoxList[i].value())
            entry.append(self.networkLabelList[i].text())
            #print(self.networkLabelList[i].text())

            self.toConfigNetworkParamList.append(entry)


        for i in range(0, self.numNetworkFactors):
            print(self.toConfigNetworkParamList[i])

        self.toConfigHWParamList = []

        print("SAVING HARDWARE ACCEL FACTORS")

        for i in range(0, self.numHWFactors):
            self.toConfigHWParamList.append(self.hwValueBoxList[i].value())

        for i in range(0, self.numHWFactors):
            print(self.toConfigHWParamList[i])

        workflowScript.startWorkflow(self.programFile, InputParameters.text(), self.toConfigNetworkParamList, self.toConfigHWParamList)

    def saveToConfig(self):
        print("Saving user values to config file")

        self.toConfigNetworkParamList = []

        print("SAVING NETWORK ACCEL FACTORS")

        for i in range(0, self.numNetworkFactors):
            entry = []

            entry.append(self.netSourceBoxList[i].value())
            #print(self.netSourceBoxList[i].value())
            entry.append(self.netDestBoxList[i].value())
            #print(self.netDestBoxList[i].value())
            entry.append(self.networkValueBoxList[i].value())
            #print(self.networkValueBoxList[i].value())
            entry.append(self.networkLabelList[i].text())
            #print(self.networkLabelList[i].text())

            self.toConfigNetworkParamList.append(entry)

        for i in range(0, self.numNetworkFactors):
            print(self.toConfigNetworkParamList[i])

        self.toConfigHWParamList = []

        print("SAVING HARDWARE ACCEL FACTORS")

        for i in range(0, self.numHWFactors):
            self.toConfigHWParamList.append(self.hwValueBoxList[i].value())

        for i in range(0, self.numHWFactors):
            print(self.toConfigHWParamList[i])

        print("CALLING SAVE TO PARAMETERS FUNCTION")

        workflowScript.saveParameters(self.toConfigNetworkParamList, self.toConfigHWParamList, self.savedConfigFileName.text())

    ############################################################################


    ############################################################################
    ##                                                                        ##
    ##                             GUI ELEMENTS                               ##
    ##                                                                        ##
    ############################################################################
    def createTopLeftGroupBox(self):
        self.topLeftGroupBox = QGroupBox("Simulated Program")

        global filePath
        filePath = QLabel()

        FileSelectButton = QPushButton("Select source file(s) directory", self)
        FileSelectButton.clicked.connect(self.selectProgramFile)

        ParameterLabelButton = QPushButton("Enter input parameters below", self)

        global InputParameters
        InputParameters = QLineEdit()
        InputParameters.setPlaceholderText('Ex: -g -verbose -etc')

        layout = QVBoxLayout()
        layout.addWidget(FileSelectButton)
        layout.addWidget(filePath)
        layout.addWidget(ParameterLabelButton)
        layout.addWidget(InputParameters)
        layout.addStretch(1)
        self.topLeftGroupBox.setLayout(layout)

    def createTopRightGroupBox(self):
        self.topRightGroupBox = QGroupBox("Simulator")

        self.startSimulationButton = QPushButton("START SIMULATION")
        self.startSimulationButton.clicked.connect(self.startSimulation)

        self.saveToConfigButton = QPushButton("Save parameters to config file")
        self.saveToConfigButton.clicked.connect(self.saveToConfig)

        self.savedConfigFileName = QLineEdit()
        self.savedConfigFileName.setPlaceholderText('Enter desired config filename here')

        layout = QVBoxLayout()
        layout.addWidget(self.startSimulationButton)
        layout.addWidget(self.saveToConfigButton)
        layout.addWidget(self.savedConfigFileName)
        layout.addStretch(1)
        self.topRightGroupBox.setLayout(layout)

    def createBottomLeftGroupBox(self, num_NetworkFactors):
        self.bottomLeftGroupBox = QGroupBox("Network Acceleration Factors")
        self.bottomLeftGroupBox.setCheckable(True)
        self.bottomLeftGroupBox.setChecked(True)

        layout = QGridLayout()

        #List of labels and value boxes generated dynamically based on num_NetworkFactors
        #
        #networkValueBoxList is a list that hold all the acceleration factor values
        self.networkLabelList = [QLabel('Network ' + str(i + 1) + ':') for i in range(num_NetworkFactors)]
        self.networkValueBoxList = [QDoubleSpinBox(self.bottomLeftGroupBox) for i in range(num_NetworkFactors)]

        self.netSourceBoxList = [QSpinBox(self.bottomLeftGroupBox) for i in range(num_NetworkFactors)]
        self.netDestBoxList = [QSpinBox(self.bottomLeftGroupBox) for i in range(num_NetworkFactors)]


        # Iterates through the list of GUI elements and adds them to the sub-gridlayout
        #
        # counter i is used to indicate which "row" of the grid layout the GUI element will be added to
        i = 0
        y = 0
        for networkLabels, networkValueBoxes, sources, dests in zip(self.networkLabelList, self.networkValueBoxList, self.netSourceBoxList, self.netDestBoxList):
            networkLabels.setAlignment(QtCore.Qt.AlignCenter)
            # Add label to top position of row "i" in the grid
            layout.addWidget(networkLabels, i, 0)

            rankText = QLabel('Rank')
            rankText.setAlignment(QtCore.Qt.AlignCenter)
            layout.addWidget(rankText, i, 1)

            # Set max and initial values for value box
            networkValueBoxes.setMaximum(1000000)
            networkValueBoxes.setValue(1)

            # Add value box directly below its label in row "i + 1" in the grid
            layout.addWidget(networkValueBoxes, i + 1, 0, 1, 5, QtCore.Qt.AlignTop)
            # RowStretch workaround to align the value box directly under the label
            layout.setRowStretch(i + 1, 1)

            #set network source box
            sources.setMaximum(1000)
            sources.setValue(y)
            layout.addWidget(sources, i, 2)

            toText = QLabel('to')
            toText.setAlignment(QtCore.Qt.AlignCenter)
            layout.addWidget(toText, i, 3)

            #set network dest box
            dests.setMaximum(1000)
            dests.setValue(y+1)
            layout.addWidget(dests, i, 4)

            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setLineWidth(1)
            layout.addWidget(separator, i + 2, 0, 1, 5, QtCore.Qt.AlignTop)
            layout.setRowStretch(i + 2, 10)

            i += 3
            y += 1

        self.bottomLeftGroupBox.setLayout(layout)

        self.scrollNetworkWindow = QScrollArea()
        self.scrollNetworkWindow.setWidget(self.bottomLeftGroupBox)
        self.scrollNetworkWindow.setWidgetResizable(True)
        self.scrollNetworkWindow.setFixedHeight(400)
        self.scrollNetworkWindow.setFixedWidth(350)

    def createConfigBottomLeftGroupBox(self, num_NetworkFactors):
        self.bottomLeftGroupBox = QGroupBox("Network Acceleration Factors")
        self.bottomLeftGroupBox.setCheckable(True)
        self.bottomLeftGroupBox.setChecked(True)

        layout = QGridLayout()

        #List of labels and value boxes generated dynamically based on num_NetworkFactors
        #
        #networkValueBoxList is a list that hold all the acceleration factor values
        self.networkLabelList = [QLabel('Network ' + str(i + 1) + ':') for i in range(num_NetworkFactors)]
        self.networkValueBoxList = [QDoubleSpinBox(self.bottomLeftGroupBox) for i in range(num_NetworkFactors)]

        self.netSourceBoxList = [QSpinBox(self.bottomLeftGroupBox) for i in range(num_NetworkFactors)]
        self.netDestBoxList = [QSpinBox(self.bottomLeftGroupBox) for i in range(num_NetworkFactors)]


        # Iterates through the list of GUI elements and adds them to the sub-gridlayout
        #
        # counter i is used to indicate which "row" of the grid layout the GUI element will be added to
        i = 0
        y = 0
        for networkLabels, networkValueBoxes, sources, dests in zip(self.networkLabelList, self.networkValueBoxList, self.netSourceBoxList, self.netDestBoxList):
            networkLabels.setAlignment(QtCore.Qt.AlignCenter)
            # Add label to top position of row "i" in the grid
            layout.addWidget(networkLabels, i, 0)

            rankText = QLabel('Rank')
            rankText.setAlignment(QtCore.Qt.AlignCenter)
            layout.addWidget(rankText, i, 1)

            # Set max and initial values for value box
            networkValueBoxes.setMaximum(1000000)
            networkValueBoxes.setValue(self.network_connections[y][2])

            # Add value box directly below its label in row "i + 1" in the grid
            layout.addWidget(networkValueBoxes, i + 1, 0, 1, 5, QtCore.Qt.AlignTop)
            # RowStretch workaround to align the value box directly under the label
            layout.setRowStretch(i + 1, 1)

            #set network source box
            sources.setMaximum(1000)
            sources.setValue(self.network_connections[y][0])
            layout.addWidget(sources, i, 2)

            toText = QLabel('to')
            toText.setAlignment(QtCore.Qt.AlignCenter)
            layout.addWidget(toText, i, 3)

            #set network dest box
            dests.setMaximum(1000)
            dests.setValue(self.network_connections[y][1])
            layout.addWidget(dests, i, 4)

            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setLineWidth(1)
            layout.addWidget(separator, i + 2, 0, 1, 5, QtCore.Qt.AlignTop)
            layout.setRowStretch(i + 2, 10)

            i += 3
            y += 1

        self.bottomLeftGroupBox.setLayout(layout)

        self.scrollNetworkWindow = QScrollArea()
        self.scrollNetworkWindow.setWidget(self.bottomLeftGroupBox)
        self.scrollNetworkWindow.setWidgetResizable(True)
        self.scrollNetworkWindow.setFixedHeight(400)
        self.scrollNetworkWindow.setFixedWidth(350)


    def createBottomRightGroupBox(self, num_HWFactors):
        self.bottomRightGroupBox = QGroupBox("Hardware Acceleration Factors")
        self.bottomRightGroupBox.setCheckable(True)
        self.bottomRightGroupBox.setChecked(True)

        layout = QGridLayout()

        # List of labels and value boxes generated dynamically based on num_HWFactors
        #
        # hwValueBoxList is a list that hold all the acceleration factor values
        self.hwLabelList = [QLabel('HW Rank ' + str(i)) for i in range(num_HWFactors)]
        self.hwValueBoxList = [QDoubleSpinBox(self.bottomRightGroupBox) for i in range(num_HWFactors)]

        # Iterates through the list of GUI elements and adds them to the sub-gridlayout
        #
        # counter i is used to indicate which "row" of the grid layout the GUI element will be added to
        i = 0
        for hwLabels, hwValueBoxes in zip(self.hwLabelList, self.hwValueBoxList):
            # Add label to top position of row "i" in the grid
            layout.addWidget(hwLabels, i, 0, QtCore.Qt.AlignTop)

            # Set max and initial values for value box
            hwValueBoxes.setMaximum(1000000)
            hwValueBoxes.setValue(1)

            # Add value box directly below its label in row "i + 1" in the grid
            layout.addWidget(hwValueBoxes, i + 1, 0, QtCore.Qt.AlignTop)
            # RowStretch workaround to align the value box directly under the label
            layout.setRowStretch(i + 1, 1)

            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setLineWidth(1)
            layout.addWidget(separator, i + 2, 0, QtCore.Qt.AlignTop)
            layout.setRowStretch(i + 2, 10)

            i += 3

        self.bottomRightGroupBox.setLayout(layout)

        self.scrollhwWindow = QScrollArea()
        self.scrollhwWindow.setWidget(self.bottomRightGroupBox)
        self.scrollhwWindow.setWidgetResizable(True)
        self.scrollhwWindow.setFixedHeight(400)
        self.scrollhwWindow.setFixedWidth(300)

    def createConfigBottomRightGroupBox(self, num_HWFactors):
        self.bottomRightGroupBox = QGroupBox("Hardware Acceleration Factors")
        self.bottomRightGroupBox.setCheckable(True)
        self.bottomRightGroupBox.setChecked(True)

        layout = QGridLayout()

        # List of labels and value boxes generated dynamically based on num_HWFactors
        #
        # hwValueBoxList is a list that hold all the acceleration factor values
        self.hwLabelList = [QLabel('HW Rank ' + str(i)) for i in range(num_HWFactors)]
        self.hwValueBoxList = [QDoubleSpinBox(self.bottomRightGroupBox) for i in range(num_HWFactors)]

        # Iterates through the list of GUI elements and adds them to the sub-gridlayout
        #
        # counter i is used to indicate which "row" of the grid layout the GUI element will be added to
        i = 0
        y = 0
        for hwLabels, hwValueBoxes in zip(self.hwLabelList, self.hwValueBoxList):
            # Add label to top position of row "i" in the grid
            layout.addWidget(hwLabels, i, 0, QtCore.Qt.AlignTop)

            # Set max and initial values for value box
            hwValueBoxes.setMaximum(1000000)
            hwValueBoxes.setValue(self.hardware_nodes[y])

            # Add value box directly below its label in row "i + 1" in the grid
            layout.addWidget(hwValueBoxes, i + 1, 0, QtCore.Qt.AlignTop)
            # RowStretch workaround to align the value box directly under the label
            layout.setRowStretch(i + 1, 1)

            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setLineWidth(1)
            layout.addWidget(separator, i + 2, 0, QtCore.Qt.AlignTop)
            layout.setRowStretch(i + 2, 10)

            i += 3
            y += 1

        self.bottomRightGroupBox.setLayout(layout)

        self.scrollhwWindow = QScrollArea()
        self.scrollhwWindow.setWidget(self.bottomRightGroupBox)
        self.scrollhwWindow.setWidgetResizable(True)
        self.scrollhwWindow.setFixedHeight(400)
        self.scrollhwWindow.setFixedWidth(300)

    ############################################################################


class Starter_GUI(QDialog):
    #CONSTRUCTOR FOR MAIN GUI WINDOW
    def __init__(self):
        super().__init__()
        
        self.originalPalette = QApplication.palette()

        self.numNetLabel = QLabel('Number of Network Types')
        self.numNetBox = QSpinBox()
        self.numNetBox.setMaximum(100)
        self.numNetBox.setValue(1)

        self.numHWLabel = QLabel('Number of MPI Ranks')
        self.numHWBox = QSpinBox()
        self.numHWBox.setMaximum(100)
        self.numHWBox.setValue(1)

        self.numNetLabel.setBuddy(self.numNetBox)
        self.numHWLabel.setBuddy(self.numHWBox)

        self.startSimulatorButton = QPushButton('Start simulator GUI')
        self.startSimulatorButton.clicked.connect(self.startSimulator)

        self.loadFromConfigButton = QPushButton('Open from config file')
        self.loadFromConfigButton.clicked.connect(self.openFromConfig)

        verticalSpacer = QSpacerItem(20, 10)
        verticalSpacer2 = QSpacerItem(20, 20)

        mainLayout = QGridLayout()
        mainLayout.addWidget(self.numNetLabel)
        mainLayout.addWidget(self.numNetBox)

        mainLayout.addItem(verticalSpacer)

        mainLayout.addWidget(self.numHWLabel)
        mainLayout.addWidget(self.numHWBox)

        mainLayout.addItem(verticalSpacer2)

        mainLayout.addWidget(self.startSimulatorButton)
        mainLayout.addWidget(self.loadFromConfigButton)


        mainLayout.setRowStretch(1, 2)
        mainLayout.setRowStretch(2, 1)
        mainLayout.setColumnStretch(0, 1)
        mainLayout.setColumnStretch(1, 1)
        self.setLayout(mainLayout)

        self.setWindowTitle("MPI Performance Co-Simulator")
        #self.changeStyle('Fusion')

    def startSimulator(self):
        print("starting simulator")
        self.simulator_gui = MPI_Simulator_GUI(self.numNetBox.value(), self.numHWBox.value())
        self.simulator_gui.show()

    def openFromConfig(self):
        print("trying to load config file")
        self.configFile = QFileDialog.getOpenFileName(self, 'Open File')
        print(self.configFile[0])
        self.network_connections, self.hardware_nodes = workflowScript.loadParameters(self.configFile[0])
        print("Read following values from config file")
        print(self.network_connections)
        print(self.hardware_nodes)

        print("starting simulator with loaded config values")
        self.simulator_gui = MPI_Simulator_GUI(len(self.network_connections), len(self.hardware_nodes), self.network_connections, self.hardware_nodes,)
        self.simulator_gui.show()

if __name__ == '__main__':

    app = QApplication(sys.argv)

    # MAIN_GUI = MPI_Simulator_GUI(3, 8)
    # MAIN_GUI.show()

    starter_gui = Starter_GUI()
    starter_gui.show()

    #MAIN_GUI.close()

    #print(MAIN_GUI.spinBox.value())

    sys.exit(app.exec_()) 
