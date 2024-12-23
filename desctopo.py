from collections import namedtuple, OrderedDict
from abc import ABC, abstractmethod
import pathlib
from ruamel.yaml import YAML
import json
import os

yaml = YAML(typ='rt')

# Helper Functions

#  endptPresent returns a boolean flag indicating whether an endpoint frame given as an argument
#  exists already in a list of endpoint frames given as another argument
def endptPresent(endptList, endpt):
    returnBool = False
    for endptInList in endptList:
        if (endptInList.Name == endpt.Name):
            returnBool = True
    return returnBool

# routerPresent returns a boolean flag indicating whether
# a router provided as input exists already in a list of routers
# also provided as input
def routerPresent(rtrList, rtr):
    returnBool = False
    for rtrInList in rtrList:
        if (rtrInList.Name == rtr.Name):
            returnBool = True
    return returnBool

# switchPresent returns a boolean flag indicating whether
# a switch provided as input exists already in a list of switches
# also provided as input
def switchPresent(swtchList, swtch):
    returnBool = False
    for swtchInList in swtchList:
        if (swtchInList.Name == swtch.Name):
            returnBool = True
    return returnBool

# A DevExecDesc struct holds a description of a device operation timing.
# ExecTime is the time (in seconds), it depends on attribute Model
DevExecDesc = namedtuple('DevExecDesc', ['devop', 'model', 'exectime'])

# A DevExecList holds a map (Times) whose key is the operation
# of a device, and whose value is a list of DevExecDescs
# associated with that operation.
# ListName is an identifier for this collection of timings
# key is the device operation.  Each has a list
# of descriptions of the timing of that operation, as a function of device model
DevExecList = namedtuple('DevExecList', ['listname', 'times'])

class DevExecListClass:
    def __init__(self):
        self.DevExecList = None
        # yaml.representer(OrderedDict, represent_ordereddict)

    # WriteToFile stores the DevExecList struct to the file whose name is given.
    # Serialization to json or to yaml is selected based on the extension of this name.
    def WriteToFile(self, filename: str):
        pathExt = pathlib.Path(filename).suffix

        with open(filename, 'w') as file:
            if (pathExt == ".yaml" or pathExt == ".YAML" or pathExt == ".yml"):
                yaml.dump(self.DevExecList, file)
            elif (pathExt == ".json" or pathExt == ".JSON"):
                file.write(json.dumps(self.DevExecList))

    # AddTiming takes the parameters of a DevExecDesc, creates one, and adds it to the FuncExecList
    def AddTiming(self, devOp: str, model: str, execTime: float):
        present = devOp in self.DevExecList['times'].keys()
        if present == False:
            self.DevExecList['times'][devOp] = []
        self.DevExecList['times'][devOp].append({"devop": devOp, "model": model, "exectime": execTime})
        # print(type(self.DevExecList[1]))

# CreateDevExecList is an initialization constructor.
# Its output struct has methods for integrating data.
def CreateDevExecList(listname: str) -> DevExecListClass:
    dev = DevExecListClass()
    dev.DevExecList = dict({"listname": listname, "times": dict()})
    return dev

# ReadDevExecList deserializes a byte slice holding a representation of an DevExecList struct.
# If the input argument of dict (those bytes) is empty, the file whose name is given is read
# to acquire them.  A deserialized representation is returned, or an error if one is generated
# from a file read or the deserialization.
def ReadDevExecList(filename: str, useYAML: bool, dictBuffer: bytes) -> DevExecListClass:

    # if the dict slice of bytes is empty we get them from the file whose name is an argument
    if (len(dictBuffer) == 0):
        with open(filename, 'rb') as file:
            dictBuffer = file.read()
    
    example = DevExecListClass()
    if (useYAML):
        example.DevExecList = yaml.load(dictBuffer)
    else:
        example.DevExecList = json.load(dictBuffer) #TODO: Fix for json
    return example


class TopoCfgClass:
    def __init__(self):
        self.TopoCfg = None
        # yaml.representer(OrderedDict, represent_ordereddict)
    
    # WriteToFile serializes the TopoCfg and writes to the file whose name is given as an input argument.
    # Extension of the file name selects whether serialization is to json or to yaml format.
    def WriteToFile(self, filename):
        pathExt = pathlib.Path(filename).suffix

        with open(filename, 'w') as file:
            if (pathExt == ".yaml" or pathExt == ".YAML" or pathExt == ".yml"):
                # yaml.dump(namedtuple_to_dict(self.TopoCfg), file)
                yaml.dump(self.TopoCfg, file)
            elif (pathExt == ".json" or pathExt == ".JSON"):
                file.write(json.dumps(self.TopoCfg))
            
# ReadTopoCfg deserializes a slice of bytes into a TopoCfg.  If the input arg of bytes
# is empty, the file whose name is given as an argument is read.  Error returned if
# any part of the process generates the error.
def ReadTopoCfg(topoFileName: str, useYAML: bool, dictBuffer: bytes) -> TopoCfgClass:
    # if the dict slice of bytes is empty we get them from the file whose name is an argument
    if (len(dictBuffer) == 0):
        with open(topoFileName, 'rb') as file:
            dictBuffer = file.read()
    
    example = TopoCfgClass()
    if (useYAML):
        example.TopoCfg = yaml.load(dictBuffer)
    else:
        example.TopoCfg = json.load(dictBuffer) #TODO: Added support for json
    return example

# numberOfIntrfcs (and more generally, numberOf{Objects}
# are counters of the number of default instances of each
# object type have been created, and so can be used
# to help create unique default names for these objects
# Not currently used at initialization, see if useful for the simulation

numberOfIntrfcs = 0 
numberOfRouters = 0 
numberOfSwitches = 0 
numberOfEndpts = 0 

# maps that let you use a name to look up an object
objTypeByName = dict()
devByName = dict()
netByName = dict() 
rtrByName = dict() 

# devConnected gives for each NetDev device a list of the other NetDev devices
# it connects to through wired interfaces
devConnected = dict() 

# IntrfcDesc defines a serializable description of a network interface
# IntrfcDesc = namedtuple("IntrfcDesc", ["name", "groups", "devtype", "mediatype", "device", "cable", "carry", "wireless", "faces"])
class IntrfcDescClass:
    def __init__(self):
        self.Name = None
        self.Groups = []
        self.DevType = None
        self.MediaType = None
        self.Device = None
        self.Cable = None
        self.Carry = []
        self.Wireless = []
        self.Faces = None

# IntrfcFrame gives a pre-serializable description of an interface, used in model construction.
# 'Almost' the same as IntrfcDesc, with the exception of one pointer
# IntrfcFrame = namedtuple("IntrfcFrame", ["name", "groups" ,"devtype", "mediatype", "device", "cable" ,"carry", "wireless", "faces"])
class IntrfcFrameClass:
    def __init__(self):
        self.Name = None
        self.Groups = []
        self.DevType = None
        self.MediaType = None
        self.Device = None
        self.Cable = None
        self.Carry = []
        self.Wireless = []
        self.Faces = None

    def AddGroup(self, groupName: str):
        if groupName not in self.Groups:
            self.Groups.append(groupName)

    def Transform(self):
        intrfcDesc = IntrfcDescClass()
        intrfcDesc.Device = self.Device
        intrfcDesc.Name = self.Name
        intrfcDesc.DevType = self.DevType
        intrfcDesc.MediaType = self.MediaType
        intrfcDesc.Faces = self.Faces
        intrfcDesc.Groups = self.Groups
        # intrfcDesc.Carry = self.Carry
        # intrfcDesc.Carry = self.Wireless

	    # a IntrfcDesc defines its Cable field to be a string, which
	    # we set here to be the name of the interface the IntrfcFrame version
	    # points to
        if (self.Cable != None):
            intrfcDesc.Cable = self.Cable.Name

	    # a IntrfcDesc defines its Carry field to be a string, which
	    # we set here to be the name of the interface the IntrfcFrame version
	    # points to
        for carry in self.Carry:
            intrfcDesc.Carry.append(carry)

        for connection in self.Wireless:
            intrfcDesc.Wireless.append(connection)

        return intrfcDesc


# DefaultIntrfcName generates a unique string to use as a name for an interface.
# That name includes the name of the device endpting the interface and a counter
def DefaultIntrfcName(device: str) -> str:
    return "intrfc@{}[.{}]".format(device, numberOfIntrfcs)

# CableIntrfcFrames links two interfaces through their 'Cable' attributes
def CableIntrfcFrames(intrfc1, intrfc2):
    intrfc1.cable = intrfc2
    intrfc2.cable = intrfc1

# CarryIntrfcFrames links two interfaces through their 'Cable' attributes
def CarryIntrfcFrames(intrfc1, intrfc2):
    found = False
    for carry in intrfc1.Carry:
        if (carry.Name == intrfc2.Name):
            found = True
            break
    if not found:
        intrfc1.Carry.append(intrfc2)
    
    found = False
    for carry in intrfc2.Carry:
        if (carry.Name == intrfc1.Name):
            found = True
            break
    if not found:
        intrfc2.Carry.append(intrfc1)

# CreateIntrfc is a constructor for [IntrfcFrame] that fills in most of the attributes except Cable.
# Arguments name the device holding the interface and its type, the type of communication fabric the interface uses, and the
# name of the network the interface connects to
def CreateIntrfc(device: str, name: str, devType: str, mediaType: str, faces:str) -> IntrfcFrameClass:
    intrfc = IntrfcFrameClass()

    # counter used in the generation of default names
    numberOfIntrfcs += 1

    # an empty string given as name flags that we should create a default one.
    if (len(name) == 0):
        name = DefaultIntrfcName(device)
    
    intrfc.Device = device
    intrfc.Name = name
    intrfc.DevType = devType
    intrfc.MediaType = mediaType
    intrfc.Faces = faces
    intrfc.Wireless = []
    intrfc.Groups = []

	# if the device in which this interface is embedded is not a router we are done
    if (devType == "Router"):

        # embedded in a router. Get its frame and that of the network which is faced
        rtr = devByName[device] #TODO: Figure out interface
        net = netByName[faces]

    # before adding the router to the network's list of routers, check for duplication
	# (based on the router's name)
    duplicated = False
    for storedRouter in net.Routers:
        if (rtr.Name == storedRouter.Name):
            duplicated = True
            break

    if not duplicated:
        net.Routers.append(rtr)

    return intrfc 

# To most easily serialize and deserialize the various structs involved in creating
# and communicating a simulation model, we ensure that they are all completely
# described without pointers, every structure is fully instantiated in the description.
# On the other hand it is easily to manage the construction of complicated structures
# under the rules Golang uses for memory management if we allow pointers.
# Our approach then is to define two respresentations for each kind of structure.  One
# has the final appellation of 'Frame', and holds pointers.  The pointer free version
# has the final  appellation of 'Desc'.   After completely building the structures using
# Frames we transform each into a Desc version for serialization.

# The NetDevice interface lets us use common code when network objects
# (endpt, switch, router, network) are involved in model construction.
class NetDevice(ABC):
    @abstractmethod
    def DevName(self) -> str: # returns the .Name field of the struct
        pass

    @abstractmethod
    def DevID(self) -> str: # returns a unique (string) identifier for the struct
        pass

    @abstractmethod
    def DevType(self) -> str: # returns the type ("Switch","Router","Endpt","Network")
        pass

    @abstractmethod
    def DevInterfaces(self): # list of interfaces attached to the NetDevice, if any
        pass
    
    @abstractmethod
    def DevAddIntrfc(self, *IntrfcFrame): # function to add another interface to the netDevic3
        pass

class EndptDescClass:
    def __init__(self):
        self.Name = None
        self.Groups = []
        self.Model = None
        self.Cores = 0
        self.Interfaces = []

class EndptFrameClass(NetDevice):
    def __init__(self):
        self.Name = None
        self.Groups = []
        self.Model = None
        self.Cores = 0
        self.Interfaces = []

    # AddGroup adds a group name to an endpoint frame's list of groups, if not already present
    def AddGroup(self, groupName: str):
        if groupName not in self.Groups:
            self.Groups.append(groupName)

    # SetEUD includes EUD into the group list
    def SetEUD(self):
        self.AddGroup("EUD")

    # IsEUD indicates whether EUD is in the group list
    def IsEUD(self):
        return any(x == "EUD" for x in self.Groups)
    
    # SetHost includes Host into the group list
    def SetHost(self):
        self.AddGroup("Host")

    # IsHost indicates whether Host is in the group list
    def IsHost(self):
        return any(x == "Host" for x in self.Groups)

    # SetSrvr adds Server to the endpoint groups list
    def SetSrvr(self):
        self.AddGroup("Server")
    
    # IsSrvr indicates whether Server is in the endpoint groups list
    def IsSrver(self):
        return any(x == "Server" for x in self.Groups)

    # SetCores records in the endpoint frame the number of cores the model assumes are available
    # for concurrent processing
    def SetCores(self, core: int):
        self.Cores = core

    def DevName(self):
        return self.Name
    
    def DevID(self):
        return self.Name
    
    def DevType(self):
        return "Endpt"

    def DevModel(self):
        return self.Model

    def DevInterfaces(self):
        return self.Interfaces
    
    # Transform returns a serializable EndptDesc, transformed from a EndptFrame.
    def Transform(self):
        hd = EndptDescClass()
        hd.Name = self.Name
        hd.Model = self.Model
        hd.Groups = self.Groups
        hd.Cores = self.Cores
        hd.Interfaces = []

	    # serialize the interfaces by calling the interface transformation function
        for interface in self.Interfaces: # interface is IntrfcFrameClass
            hd.Interfaces.append(interface.Transform())

        return hd
    
    # AddIntrfc includes a new interface frame for the endpt.
    # An error is reported if this specific (by pointer value or by name) interface is already connected.
    def AddIntrfc(self, iff):
        returnError = None
        for ih in self.Interfaces:
            if (ih == iff or ih.Name == iff.Name):
                returnError = "attempt to re-add interface {} to endpt {}".format(iff.Name, self.Name)
    
        if (returnError == None):

	        # ensure that interface states its presence on this device
            iff.DevType = "Endpt"
            iff.Device = self.Name

	        # save the interface
            self.Interfaces.append(iff)

        return returnError

def DefaultEndptName(etype: str):
    return "{}-endpt.({})".format(etype, numberOfEndpts)

# CreateEndpt is a constructor. It saves (or creates) the endpt name, and saves
# the optional endpt type (which has use in run-time configuration)
def CreateEndpt(name:str, etype: str, model: str, cores: int):
    epf = EndptFrameClass()
    numberOfEndpts = numberOfEndpts + 1
    
    epf.Model = model
    epf.Cores = cores

	# get a (presumeably unique) string name
    if (len(name) == 0):
        name = DefaultEndptName(etype)

    epf.Name = name
    objTypeByName[name] = "Endpt"
    devByName[name] = epf

    epf.Interfaces = []
    epf.Groups = []

    return epf

# CreateHost is a constructor.  It creates an endpoint frame that sets the Host flag
def CreateHost(name: str, model: str, cores: int):
    host = CreateEndpt(name, "Host", model, cores)
    host.AddGroup("Host")
    return host

# CreateNode is a constructor.  It creates an endpoint frame, does not mark with Host, Server, or EUD
def CreateNode(name: str, model: str, cores: int):
    return CreateEndpt(name, model, cores)

# CreateSensor is a constructor.
def CreateSensor(name: str, model: str):
    sensor = CreateEndpt(name, "Sensor", model, 1)
    sensor.AddGroup("Sensor")
    return sensor

# CreateSrvr is a constructor.  It creates an endpoint frame and marks it as a server
def CreateSrvr(name: str, model: str, cores: int):
    endpt = CreateEndpt(name, "Srvr", model, cores)
    endpt.AddGroup("Server")
    return endpt

# CreateEUD is a constructor.  It creates an endpoint frame with the EUD flag set to true
def CreateEUD(name: str, model: str, cores: int):
    epf = CreateEndpt(name, "EUD", model, cores)
    epf.AddGroup("EUD")
    return epf

   
class RouterDescClass():
    def __init__(self):
        self.Name = None
        self.Groups = []
        self.Model = None
        self.Interfaces = []

class RouterFrameClass(NetDevice):
    def __init__(self):
        self.Name = None
        self.Groups = []
        self.Model = None
        self.Interfaces = []
    
    def AddIntrfc(self, intrfc):
        returnError = None
        for ih in self.Interfaces:
            if (ih == intrfc or ih.Name == intrfc.Name):
                returnError = "attempt to re-add interface {} to router {}".format(intrfc.Name, self.Name)
    
        if (returnError == None):

	        #  ensure that the interface has stored the home device type and name
            intrfc.DevType = "Router"
            intrfc.Device = self.Name

	        # save the interface
            self.Interfaces.append(intrfc)

        return returnError

    def DevAddIntrfc(self, iff):
        return self.AddIntrfc(iff)
    
    def AddGroup(self, groupName):
        if groupName not in self.Groups:
            self.Groups.append(groupName)

    def Transform(self):
        rd = RouterDescClass()
        rd.Name = self.Name
        rd.Model = self.Model
        rd.Groups = self.Groups
        rd.Cores = self.Cores
        rd.Interfaces = []

	    # serialize the interfaces by calling the interface transformation function
        for interface in self.Interfaces: # interface is IntrfcFrameClass
            rd.Interfaces.append(interface.Transform())

        return rd

    def DevName(self):
        return self.Name

    def DevID(self):
        return self.Name

    def DevType(self):
        return "Router"

    def DevModel(self):
        return self.Model

    def DevInterfaces(self):
        return self.Interfaces

# DefaultRouterName returns a unique name for a router
def DefaultRouterName():
	return "rtr.[{}]".format(numberOfRouters)

def CreateRouter(name: str, model: str):
    rtr = RouterFrameClass()
    numberOfRouters = numberOfRouters + 1

    rtr.Model = model

    if (len(name) == 0):
        name = DefaultRouterName()
    
    rtr.Name = name
    objTypeByName[name] = "Router"
    devByName[name] = rtr
    rtrByName[name] = rtr
    rtr.Interfaces = []
    rtr.Groups = []

    return rtr

class SwitchDescClass():
    def __init__(self):
        self.Name = None
        self.Groups = []
        self.Model = None
        self.Interfaces = []

class SwitchFrameClass(NetDevice):
    def __init__(self):
        self.Name = None
        self.Groups = []
        self.Model = None
        self.Interfaces = []

    # AddGroup adds a group to a switch's list of groups, if not already present in that list
    def AddGroup(self, groupName: str):
        if groupName not in self.Groups:
            self.Groups.append(groupName)

    # AddIntrfc includes a new interface frame for the switch.  Error is returned
    # if the interface (or one with the same name) is already attached to the SwitchFrame
    def AddIntrfc(self, iff):
        returnError = None
        for ih in self.Interfaces:
            if (ih == iff or ih.Name == iff.Name):
                returnError = "attempt to re-add interface {} to switch {}".format(iff.Name, self.Name)
    
        if (returnError == None):

	        # ensure that interface states its presence on this device
            iff.DevType = "Switch"
            iff.Device = self.Name

	        # save the interface
            self.Interfaces.append(iff)

        return returnError

    def Transform(self):
        sd = SwitchDescClass()
        sd.Name = self.Name
        sd.Model = self.Model
        sd.Groups = self.Groups
        sd.Interfaces = []

	    # serialize the interfaces by calling the interface transformation function
        for interface in self.Interfaces: # interface is IntrfcFrameClass
            sd.Interfaces.append(interface.Transform())

        return sd


    def DevName(self):
        return self.Name

    def DevID(self):
        return self.Name

    def DevType(self):
        return "Switch"

    def DevModel(self):
        return self.Model

    def DevInterfaces(self):
        return self.Interfaces


# DefaultSwitchName returns a unique name for a switch
def DefaultSwitchName(name: str):
    return "switch({}).{}".format(name, numberOfSwitches)

# CreateSwitch constructs a switch frame.  Saves (and possibly creates) the switch name,
def CreateSwitch(name: str, model: str):
    sf = SwitchFrameClass()
    numberOfSwitches = numberOfSwitches + 1

    if (len(name) == 0):
        name = DefaultSwitchName("switch")
    
    objTypeByName[name] = "Switch"
    devByName[name] = sf

    sf.Name = name
    sf.Model = model
    sf.Interfaces = []
    sf.Groups = []

    return sf

# CreateHub constructs a switch frame tagged as being a hub
def CreateHub(name: str, model: str):
    hub = CreateSwitch(name, model)
    hub.AddGroup("Hub")
    return hub

# CreateBridge constructs a switch frame tagged as being a bridge
def CreateBridge(name: str, model: str):
    bridge = CreateSwitch(name, model)
    bridge.AddGroup("Bridge")
    return bridge

# CreateRepeater constructs a switch frame tagged as being a repeateer
def CreateRepeater(name: str, model: str):
    rptr = CreateSwitch(name, model)
    rptr.AddGroup("Repeater")
    return rptr

# NetworkDesc is a serializable version of the Network information, where
# the pointers to routers, and switches are replaced by the string
# names of those entities
class NetworkDescClass():
    def __init__(self):
        self.Name = None
        self.Groups = []
        self.NetScale = None
        self.MediaType = None
        self.Routers = []
        self.Endpts = []
        self.Switches = []

# A NetworkFrame holds the attributes of a network during the model construction phase
class NetworkFrameClass(NetDevice):
    def __init__(self):
	    # Name is a unique name across all objects in the simulation. It is used universally to reference this network
        self.Name = None
        self.Groups = []

	    # NetScale describes role of network, e.g., LAN, WAN, T3, T2, T1.  Used as an attribute when doing experimental configuration
        self.NetScale = None

	    # for now the network is either "wired" or "wireless"
        self.MediaType = None
    
	    # any router with an interface that faces this network is in this list
        self.Routers = []

    	# any endpt with an interface that faces this network is in this list
        self.Endpts = []
    
	    # any endpt with an interface that faces this network is in this list
        self.Switches = []
    
    # FacedBy determines whether the device offered as an input argument
    # has an interface whose 'Faces' component references this network
    def FacedBy(self, dev):
        intrfcs = dev.DevInterfaces() #TODO: Fix this interface
        netName = self.Name
        returnBool = False
        for intrfc in intrfcs:
            if (intrfc.Faces == netName):
                returnBool = True
        return returnBool
    
    # AddGroup appends a group name to the network frame list of groups,
    # checking first whether it is already present in the list
    def AddGroup(self, groupName):
        if (groupName in self.Groups):
            self.Groups.append(groupName)
    
    # DevNetworks returns a comma-separated string of
    # of the names of networks the argument NetDevice interfaces
    # face
    def DevNetworks(self, dev):
        nets = []
        for intrfc in dev.DevInterfaces(): #TODO: Fix this interface
            nets.append(intrfc.Faces)
        return ','.join(nets)

    # IncludeDev makes sure that the network device being offered
    #
    #	a) has an interface facing the network
    #	b) is included in the network's list of those kind of devices
    def IncludeDev(self, dev, mediaType, chkIntrfc):
        devName = dev.DevName()
        devType = dev.DevType()

        returnError = None
        intrfc = None
	    # check consistency of network media type and mediaType argument.
	    # If mediaType is wireless then network must be wireless.   It is
	    # permitted though to have the network be wireless and the mediaType be wired.
        if (mediaType == "wireless" and not(self.MediaType == "wireless")):
            returnError = "including a wireless device in a wired network"
        
        if (returnError == None):
            # if the device does not have an interface pointed at the network, make one
            if (chkIntrfc and not self.FacedBy(dev)):
                intrfcName = DefaultIntrfcName(dev.DevName()) # TODO: Fix interface
                intrfc = CreateIntrfc(devName, intrfcName, devType, mediaType, self.Name)

            match devType:
                case "Endpt":
                    endpt = dev
                    if (intrfc != None):
                        endpt.Interfaces.append(intrfc)
                    if not endptPresent(self.Endpts, endpt):
                        self.Endpts.append(endpt)
                case "Router":
                    rtr = dev
                    if (intrfc != None):
                        rtr.Interfaces.append(intrfc)
                    if not routerPresent(self.Routers, rtr):
                        self.Routers.append(rtr)
                case "Switch":
                    swtch = dev
                    if (intrfc != None):
                        swtch.Interfaces.append(intrfc)
                    if not switchPresent(swtch):
                        self.Switches.append(swtch)
        
        return returnError

    # AddRouter includes the argument router into the network,
    def AddRouter(self, rtrf):

        returnError = None
        found = False
	    # check whether a router with this same name already exists here
        for rtr in self.Routers:
            if (rtr.Name == rtrf.Name):
                found = True
                break

        if not found:
            if not self.FacedBy(rtrf):
                returnError = "attempting to add router {} to network {} without prior association of an interface".format(rtrf.Name, self.Name)
            if (returnError == None):
                self.Routers.append(rtrf)
        
        return returnError

    # AddSwitch includes the argument router into the network,
    # throws an error if already present
    def AddSwitch(self, swtch):

        returnError = None
        found = False
	    # check whether a router with this same name already exists here
        for swtch in self.Switches:
            if (swtch.Name == swtch.Name):
                found = True
                break

        if not found:
            if not self.FacedBy(swtch):
                returnError = "attempting to add switch {} to network {} without prior association of an interface".format(swtch.Name, self.Name)
            if (returnError == None):
                self.Switches.append(swtch)
        
        return returnError


    # Transform converts a network frame into a network description.
    # It copies string attributes, and converts pointers to routers, and switches
    # to strings with the names of those entities
    def Transform(self):
        nd = NetworkDescClass()
        nd.Name = self.Name
        nd.NetScale = self.NetScale
        nd.MediaType = self.MediaType
        nd.Groups = self.Groups

	    # in the frame the routers are pointers to objects, now we store their names
        for rtr in self.Routers:
            nd.Routers.append(rtr.Name)
        
	    # in the frame the routers are pointers to objects, now we store their names
        for endpt in self.Endpts:
            nd.Endpts.append(endpt.Name)
        
	    # in the frame the routers are pointers to objects, now we store their names
        for swtch in self.Switches:
            nd.Switches.append(swtch.Name)

        return nd

    def DevName(self):
        return self.Name

    def DevID(self):
        return self.Name

    def DevType(self):
        return "Network"

    def DevModel(self):
        return self.Model

    def DevInterfaces(self):
        return self.Interfaces
    
# CreateNetwork is a constructor, with all the inherent attributes specified
def CreateNetwork(name: str, NetScale: str, MediaType: str):
    nf = NetworkFrameClass()
    nf.Name = name
    nf.NetScale = NetScale
    nf.MediaType = MediaType

    objTypeByName[name] = "Network"
    netByName[name] = nf

    return nf

# isConnected is part of a set of functions and data structures useful in managing
# construction of a communication network. It indicates whether two devices whose
# identities are given are already connected through their interfaces, by Cable, Carry, or Wireless
def isConnected(id1, id2):
    present = id1 in devConnected
    returnBool = False
    if not present:
        pass
    else:
        for peerID in devConnected[id1]:
            if peerID == id2:
                returnBool = True
                break
        
    return returnBool

# MarkConnected modifes the devConnected data structure to reflect that
# the devices whose identities are the arguments have been connected.
def markConnected(id1, id2):
	# if already connected there is nothing to do here
    if isConnected(id1, id2):
        pass
    else:
        # for both devices, add their names to the 'connected to' list of the other
	    # complete the data structure for devConnected[id1][id2] if need be
        present = id1 in devConnected
        if not present:
            devConnected[id1] = []
        devConnected[id1].append(id2)
        
	    # complete the data structure for devConnected[id2][id1] if need be
        present = id2 in devConnected
        if not present:
            devConnected[id2] = []
        devConnected[id2].append(id1)

# determine whether intrfc1 is in the Carry slice of intrfc2
def carryContained(intrfc1, intrfc2):
    returnBool = False
    for intrfc in intrfc2.Carry:
        if (intrfc == intrfc1 or intrfc.Name == intrfc1.Name):
            returnBool = True
            break
    return returnBool

# ConnectDevs establishes a 'cabled' or 'carry' connection (creating interfaces if needed) between
# devices dev1 and dev2 (recall that NetDevice is an interface satisified by Endpt, Router, Switch)
def ConnectDevs(dev1, dev2, cable, faces):
	# if already connected there is nothing to do here
    if isConnected(dev1.DevID(), dev2.DevID()):
        return
    
    # this call will record the connection
    markConnected(dev1.DevID(), dev2.DevID())

    # ensure that both devices are known to the network
    net = netByName[faces]
    net.IncludeDev(dev1, "wired", True)
    net.IncludeDev(dev2, "wired", True)

    # for each device collect all the interfaces that face the named network and are not wireless
    intrfcs1 = []
    intrfcs2 = []

    for intrfc in dev2.DevInterfaces():
        if (intrfc.Faces == faces and not intrfc.MediaType == "wireless"):
            intrfcs2.append(intrfc)

    for intrfc in dev1.DevInterfaces():
        if (intrfc.Faces == faces and not intrfc.MediaType == "wireless"):
            intrfcs1.append(intrfc)

    # check whether the connection requested exists already or we can complete it
    # without creating new interfaces
    if cable:
        for intrfc1 in intrfcs1:
            for intrfc2 in intrfcs2:

                # keep looping if we're looking for cable and they don't match
                if (cable and intrfc1.Cable != None and intrfc1.Cable != intrfc2):
                    continue

                # either intrfc1.cable is nil or intrfc is connected already to intrfc2.
                # so then if intrfc2.cable is nil or is connected to intrfc1 we can complete the connection and leave
                if (cable and (intrfc2.Cable == intrfc1 or intrfc2.Cable == None)):
                    intrfc1.Cable = intrfc2
                    intrfc2.Cable = intrfc1
                    return
    else:
		# see whether we can establish the connection without new interfaces
        for intrfc1 in intrfcs1:
            for intrfc2 in intrfcs2:
                if carryContained(intrfc1, intrfc2) and not carryContained(intrfc2, intrfc1):
                    intrfc2.Carry.append(intrfc1)
                    return
                if carryContained(intrfc2, intrfc1) and not carryContained(intrfc1, intrfc2):
                    intrfc1.Carry.append(intrfc2)
                    return
                
	# no prior reason to complete connection between dev1 and dev2
	# see whether each has a 'free' interface, meaning it
	# points to the right network but is not yet cabled or carried
    free1 = None               
    free2 = None

	# check dev1's interfaces
    for intrfc1 in intrfcs1:
		# we're looking to cable, the interface is facing the right network,
		# and it's cabling is empty
        if intrfc1.Faces == faces and intrfc1.Cable == None:
            free1 = intrfc1
            break

	# if dev1 does not have a free interface, create one
    if free1 == None:
        intrfcName = DefaultIntrfcName(dev1.DevName())
        free1 = CreateIntrfc(dev1.DevName(), intrfcName, dev1.DevType(), "wired", faces)
        dev1.DevAddIntrfc(free1)

	# check dev2's interfaces
    for intrfc2 in intrfcs2:
        if intrfc2.Faces == faces and intrfc2.Cable == None:
            free2 = intrfc2
            break

	# if dev2 does not have a free interface, create one
    if free2 == None:
        intrfcName = DefaultIntrfcName(dev2.DevName())
        free2 = CreateIntrfc(dev2.DevName(), intrfcName, dev2.DevType(), "wired", faces)
        dev2.DevAddIntrfc(free2)    

	# found the interfaces, make the connection, using cable or carry as directed by the input argument
    if cable:
        free1.Cable = free2
        free2.Cable = free1
    else:
        free1.Carry.append(free2)
        free2.Carry.append(free1)

class TopoCfgFrameClass:
    def __init__(self):
        self.TopoCfgFrame = None
    
    # addEndpt adds a Endpt to the topology configuration (if it is not already present).
    # Does not create an interface
    def addEndpt(self, endpt):
        inputName = endpt.Name
        for storedEndpt in self.TopoCfgFrame["Endpts"]:
            if (storedEndpt == endpt or storedEndpt.Name == inputName):
                return
        self.TopoCfgFrame["Endpts"].append(endpt)

    # AddNetwork adds a Network to the topology configuration (if it is not already present)
    def addNetwork(self, net):
        inputName = net.Name
        for storedNetwork in self.TopoCfgFrame["Networks"]:
            if (storedNetwork == net or storedNetwork.Name == inputName):
                return
        self.TopoCfgFrame["Networks"].append(net)
    
    # addRouter adds a Router to the topology configuration (if it is not already present)
    def addRouter(self, rtr):
        inputName = rtr.Name
        for storedRouter in self.TopoCfgFrame["Routers"]:
            if (storedRouter == rtr or storedRouter.Name == inputName):
                return
        self.TopoCfgFrame["Routers"].append(rtr)
    
    # addSwitch adds a switch to the topology configuration (if it is not already present)
    def addSwitch(self, swtch):
        inputName = swtch.Name
        for storedSwitch in self.TopoCfgFrame["Switches"]:
            if (storedSwitch == swtch or storedSwitch.Name == inputName):
                return
        self.TopoCfgFrame["Switches"].append(swtch)

    # Consolidate gathers endpts, switches, and routers from the networks added to the TopoCfgFrame,
    # and make sure that all the devices referred to in the different components are exposed
    # at the TopoCfgFrame level
    def Consolidate(self) -> str:
        errorMsg = None
        if (len(self.TopoCfgFrame["Networks"]) == 0):
            errorMsg = "no networks given in TopoCfgFrame in Consolidate call"
        else:
            self.TopoCfgFrame["Endpts"] = []
            self.TopoCfgFrame["Routers"] = []
            self.TopoCfgFrame["Switches"] = []
        
            for network in self.TopoCfgFrame["Networks"]:

                for rtr in network.Routers:
                    self.addRouter(rtr)
                for endpt in network.Endpts:
                    self.addEndpt(endpt)
                for swtch in network.Switches:
                    self.addSwitch(swtch)

        return errorMsg

    # Transform transforms the slices of pointers to network objects
    # into slices of instances of those objects, for serialization
    def Transform(self) -> TopoCfgClass:
        cerr = self.Consolidate()
        if (cerr != None):
            os.exit()
        
        td = TopoCfgClass()
        td.TopoCfg = dict()

        td.TopoCfg["Name"] = self.TopoCfgFrame["Name"]
        


def CreateTopoCfgFrame(name: str):
    tf = TopoCfgFrameClass()
    tf.TopoCfgFrame = dict({"Name": name,
                            "Endpts": [],
                            "Networks": [],
                            "Routers": [],
                            "Switches": []})

    return tf


class TopoCfgDictClass:
    def __init__(self):
        self.TopoCfgDict = None
        # yaml.representer(OrderedDict, represent_ordereddict)

    # AddTopoCfg includes a TopoCfg into the dictionary, optionally returning an error
    # if an TopoCfg with the same name has already been included
    def AddTopoCfg(self, tc, overwrite):
        if not overwrite:
            present = tc.name in self.TopoCfgDict.cfgs.keys()
            if present:
                return "attmpt to overwrite TopoCfg {} in TopoCfgDict".format(tc.name)
        
        self.TopoCfgDict.cfgs[tc.name] = tc
        return None

    # RecoverTopoCfg returns a copy (if one exists) of the TopoCfg with name equal to the input argument name.
    # Returns a boolean indicating whether the entry was actually found
    def RecoverTopoCfg(self, name) -> tuple[TopoCfgClass, bool]:
        tc = self.TopoCfgDict.cfgs.get(name)
        bool_ret = False
        if (tc != None):
            bool_ret = True
        return (tc, bool_ret)

    # WriteToFile stores the DevExecList struct to the file whose name is given.
    # Serialization to json or to yaml is selected based on the extension of this name.
    def WriteToFile(self, filename: str):
        pathExt = pathlib.Path(filename).suffix

        with open(filename, 'w') as file:
            if (pathExt == ".yaml" or pathExt == ".YAML" or pathExt == ".yml"):
                # yaml.dump(namedtuple_to_dict(self.DevExecList), file)
                yaml.dump(self.DevExecList, file)
            elif (pathExt == ".json" or pathExt == ".JSON"):
                file.write(json.dumps(self.DevExecList))

# CreateTopoCfgDict is a constructor. Saves the dictionary name, initializes the TopoCfg map.
def CreateTopoCfgDict(name: str):
    tcd = TopoCfgDictClass()
    tcd.TopoCfgDict = dict({"DictName": name, "Cfgs": dict()})
    return tcd

# ReadTopoCfgDict deserializes a slice of bytes into a TopoCfgDict.  If the input arg of bytes
# is empty, the file whose name is given as an argument is read.  Error returned if
# any part of the process generates the error.
def ReadTopoCfgDict(topoCfgDictFileName: str, useYAML: bool, dictBuffer: bytes) -> TopoCfgDictClass:
    
    # if the dict slice of bytes is empty we get them from the file whose name is an argument
    if (len(dictBuffer) == 0):
        with open(topoCfgDictFileName, 'rb') as file:
            dictBuffer = file.read()
    
    example = TopoCfgDictClass()
    if (useYAML):
        example.TopoCfgDict = yaml.load(dictBuffer)
    else:
        example.TopoCfgDict = json.load(dictBuffer) #TODO: Added support for json
    return example

class DevDescDictClass:
    def __init__(self):
        self.DevDescDict = None

    # AddDevDesc constructs a device identifier by concatenating the Manufacturer and Model
    # attributes of the argument device as the index to the referring DevDescDict
    def AddDevDesc(self, dd):
        name = dd["manufacturer"] + dd["model"]
        self.DevDescDict["DescMap"][name] = dd
    
    def RecoverDevDesc(self, name: str):
        present = name in self.DevDescDict["DescMap"].keys()
        if not present:
            os.exit()
        return self.DevDescDict["DescMap"][name]
    
    # WriteToFile stores the DevDescDict struct to the file whose name is given.
    # Serialization to json or to yaml is selected based on the extension of this name.
    def WriteToFile(self, filename: str):
        pathExt = pathlib.Path(filename).suffix

        with open(filename, 'w') as file:
            if (pathExt == ".yaml" or pathExt == ".YAML" or pathExt == ".yml"):
                # yaml.dump(namedtuple_to_dict(self.TopoCfg), file)
                yaml.dump(self.TopoCfg, file)
            elif (pathExt == ".json" or pathExt == ".JSON"):
                file.write(json.dumps(self.TopoCfg))

def CreateDevDescDict(name: str):
    ddd = DevDescDictClass()
    ddd.DevDescDict = dict({"Name": name, "DescMap": dict()})
    return ddd

def CreateDevDesc(devType: str, manufacturer: str, model: str, cores: int, freq: float, cache: float):
    devTypes = devType.split()
    dd = dict({"devtype": devTypes, "manufacturer": manufacturer, "model": model, "cores": cores, "freq": freq, "cache": cache})
    return dd

# ReadDevDescDict deserializes a byte slice holding a representation of an DevDescDict struct.
# If the input argument of dict (those bytes) is empty, the file whose name is given is read
# to acquire them.  A deserialized representation is returned, or an error if one is generated
# from a file read or the deserialization.

def ReadDecDescDict(filename: str, useYAML: bool, dictBuffer: bytes):

    # if the dict slice of bytes is empty we get them from the file whose name is an argument
    if (len(dictBuffer) == 0):
        with open(filename, 'rb') as file:
            dictBuffer = file.read()
    
    example = TopoCfgDictClass()
    if (useYAML):
        example.TopoCfgDict = yaml.load(dictBuffer)
    else:
        example.TopoCfgDict = json.load(dictBuffer) #TODO: Added support for json
    return example