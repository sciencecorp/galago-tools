# -*- coding: mbcs -*-
# Created by makepy.py version 0.5.01
# By python version 3.9.12 (main, Apr  4 2022, 05:23:19) [MSC v.1916 32 bit (Intel)]
# From type library 'AgilentBravo.dll'
# On Fri Nov 14 00:25:26 2025
'Agilent Bravo ActiveX Control module'
makepy_version = '0.5.01'
python_version = 0x3090cf0

import win32com.client.CLSIDToClass, pythoncom, pywintypes
import win32com.client.util
from pywintypes import IID
from win32com.client import Dispatch

# The following 3 lines may need tweaking for the particular server
# Candidates are pythoncom.Missing, .Empty and .ArgNotFound
defaultNamedOptArg=pythoncom.Empty
defaultNamedNotOptArg=pythoncom.Empty
defaultUnnamedArg=pythoncom.Empty

CLSID = IID('{9BBEC3D9-BF33-4A22-8F2A-EEBD110B7548}')
MajorVersion = 1
MinorVersion = 0
LibraryFlags = 10
LCID = 0x0

from win32com.client import DispatchBaseClass
class _DHomewood(DispatchBaseClass):
	'Dispatch interface for Homewood Control'
	CLSID = IID('{18C9D060-CD66-4A19-84DE-FD472156A79B}')
	coclass_clsid = IID('{C912FE20-06A6-4B7C-9BFB-F7B3EE29092E}')

	def Abort(self):
		'Aborts the current task'
		return self._oleobj_.InvokeTypes(3, LCID, 1, (3, 0), (),)

	def AboutBox(self):
		return self._oleobj_.InvokeTypes(-552, LCID, 1, (24, 0), (),)

	def Aspirate(self, Volume=defaultNamedNotOptArg, PreAspirateVolume=defaultNamedNotOptArg, PostAspirateVolume=defaultNamedNotOptArg, PlateLocation=defaultNamedNotOptArg
			, DistanceFromWellBottom=defaultNamedNotOptArg, RetractDistancePerMicroliter=defaultNamedNotOptArg):
		'Aspirates with the specified parameters'
		return self._oleobj_.InvokeTypes(14, LCID, 1, (3, 0), ((5, 0), (5, 0), (5, 0), (2, 0), (5, 0), (5, 0)),Volume
			, PreAspirateVolume, PostAspirateVolume, PlateLocation, DistanceFromWellBottom, RetractDistancePerMicroliter
			)

	def Close(self):
		'Closes the currently-initialized Bravo profile'
		return self._oleobj_.InvokeTypes(8, LCID, 1, (3, 0), (),)

	def Dispense(self, Volume=defaultNamedNotOptArg, EmptyTips=defaultNamedNotOptArg, BlowoutVolume=defaultNamedNotOptArg, PlateLocation=defaultNamedNotOptArg
			, DistanceFromWellBottom=defaultNamedNotOptArg, RetractDistancePerMicroliter=defaultNamedNotOptArg):
		'Dispenses with the specified parameters'
		return self._oleobj_.InvokeTypes(15, LCID, 1, (3, 0), ((5, 0), (11, 0), (5, 0), (2, 0), (5, 0), (5, 0)),Volume
			, EmptyTips, BlowoutVolume, PlateLocation, DistanceFromWellBottom, RetractDistancePerMicroliter
			)

	def EnumerateProfiles(self):
		'Lists all available profiles'
		return self._ApplyTypes_(10, 1, (12, 0), (), 'EnumerateProfiles', None,)

	def GetActiveXVersion(self):
		'Retrieves ActiveX version'
		# Result is a Unicode object
		return self._oleobj_.InvokeTypes(11, LCID, 1, (8, 0), (),)

	def GetDeviceConfiguration(self, DeviceConfigurationXML=defaultNamedNotOptArg):
		'Retrieves the current Bravo configuration in XML'
		return self._oleobj_.InvokeTypes(35, LCID, 1, (3, 0), ((16392, 0),),DeviceConfigurationXML
			)

	def GetFirmwareVersion(self):
		'Retrieves firmware version'
		# Result is a Unicode object
		return self._oleobj_.InvokeTypes(12, LCID, 1, (8, 0), (),)

	def GetHardwareVersion(self):
		'Retrieves hardware version'
		# Result is a Unicode object
		return self._oleobj_.InvokeTypes(13, LCID, 1, (8, 0), (),)

	def GetLabwareAtLocation(self, PlateLocation=defaultNamedNotOptArg, LabwareName=defaultNamedNotOptArg):
		'Given a deck location, retrieves the name of the labware currently there'
		return self._oleobj_.InvokeTypes(36, LCID, 1, (3, 0), ((2, 0), (16392, 0)),PlateLocation
			, LabwareName)

	def GetLastError(self):
		'Returns the last error reported by the Bravo device'
		# Result is a Unicode object
		return self._oleobj_.InvokeTypes(6, LCID, 1, (8, 0), (),)

	def HomeW(self):
		'Homes the W axis'
		return self._oleobj_.InvokeTypes(34, LCID, 1, (3, 0), (),)

	def HomeXYZ(self):
		'Homes the X, Y, and Z axes'
		return self._oleobj_.InvokeTypes(33, LCID, 1, (3, 0), (),)

	def Ignore(self):
		'Ignores the error in the current task and moves to the next state'
		return self._oleobj_.InvokeTypes(4, LCID, 1, (3, 0), (),)

	def Initialize(self, Profile=defaultNamedNotOptArg):
		'Initializes the specified Bravo profile'
		return self._oleobj_.InvokeTypes(7, LCID, 1, (3, 0), ((8, 0),),Profile
			)

	def Mix(self, Volume=defaultNamedNotOptArg, PreAspirateVolume=defaultNamedNotOptArg, BlowoutVolume=defaultNamedNotOptArg, Cycles=defaultNamedNotOptArg
			, PlateLocation=defaultNamedNotOptArg, DistanceFromWellBottom=defaultNamedNotOptArg, RetractDistancePerMicroliter=defaultNamedNotOptArg):
		'Mixes'
		return self._oleobj_.InvokeTypes(16, LCID, 1, (3, 0), ((5, 0), (5, 0), (5, 0), (2, 0), (2, 0), (5, 0), (5, 0)),Volume
			, PreAspirateVolume, BlowoutVolume, Cycles, PlateLocation, DistanceFromWellBottom
			, RetractDistancePerMicroliter)

	def MoveToLocation(self, PlateLocation=defaultNamedNotOptArg, OnlyMoveZ=defaultNamedNotOptArg):
		'Moves the Bravo head to the specified location'
		return self._oleobj_.InvokeTypes(22, LCID, 1, (3, 0), ((2, 0), (11, 0)),PlateLocation
			, OnlyMoveZ)

	def MoveToPosition(self, Axis=defaultNamedNotOptArg, Position=defaultNamedNotOptArg, Velocity=defaultNamedNotOptArg, Acceleration=defaultNamedNotOptArg):
		'Moves an axis to a location at the specified velocity and acceleration'
		return self._oleobj_.InvokeTypes(37, LCID, 1, (3, 0), ((2, 0), (5, 0), (5, 0), (5, 0)),Axis
			, Position, Velocity, Acceleration)

	def PickAndPlace(self, StartLocation=defaultNamedNotOptArg, EndLocation=defaultNamedNotOptArg, GripperOffset=defaultNamedNotOptArg, LabwareThickness=defaultNamedNotOptArg):
		'Picks a plate from StartLocation and places at EndLocation using GripperOffset'
		return self._oleobj_.InvokeTypes(30, LCID, 1, (3, 0), ((2, 0), (2, 0), (5, 0), (5, 0)),StartLocation
			, EndLocation, GripperOffset, LabwareThickness)

	def PumpReagent(self, PlateLocation=defaultNamedNotOptArg, FillReservoir=defaultNamedNotOptArg, PumpSpeed=defaultNamedNotOptArg, PumpTime=defaultNamedNotOptArg):
		'Starts the specified pump module'
		return self._oleobj_.InvokeTypes(20, LCID, 1, (3, 0), ((2, 0), (11, 0), (5, 0), (5, 0)),PlateLocation
			, FillReservoir, PumpSpeed, PumpTime)

	def RegisterRowColumn(self, Row=defaultNamedNotOptArg, Column=defaultNamedNotOptArg):
		'method RegisterRowColumn'
		return self._oleobj_.InvokeTypes(23, LCID, 1, (3, 0), ((2, 0), (2, 0)),Row
			, Column)

	def Retry(self):
		'Retries the current task'
		return self._oleobj_.InvokeTypes(5, LCID, 1, (3, 0), (),)

	def SetDispenseToWaste(self, DispenseToWasteHeight=defaultNamedNotOptArg):
		'method SetDispenseToWaste'
		return self._oleobj_.InvokeTypes(27, LCID, 1, (3, 0), ((5, 0),),DispenseToWasteHeight
			)

	def SetEndOfTaskBehavior(self, Behavior=defaultNamedNotOptArg):
		'method SetEndOfTaskBehavior'
		return self._oleobj_.InvokeTypes(29, LCID, 1, (3, 0), ((2, 0),),Behavior
			)

	def SetHeadMode(self, HeadMode=defaultNamedNotOptArg):
		'Allows user to specify how the head will be used'
		return self._oleobj_.InvokeTypes(28, LCID, 1, (3, 0), ((2, 0),),HeadMode
			)

	def SetLabwareAtLocation(self, PlateLocation=defaultNamedNotOptArg, LabwareType=defaultNamedNotOptArg):
		'method SetLabwareAtLocation'
		return self._oleobj_.InvokeTypes(24, LCID, 1, (3, 0), ((2, 0), (8, 0)),PlateLocation
			, LabwareType)

	def SetLiquidClass(self, LiquidClass=defaultNamedNotOptArg):
		'method SetLiquidClass'
		return self._oleobj_.InvokeTypes(25, LCID, 1, (3, 0), ((8, 0),),LiquidClass
			)

	def SetTipTouch(self, NumberOfSides=defaultNamedNotOptArg, RetractDistance=defaultNamedNotOptArg, HorizontalOffset=defaultNamedNotOptArg):
		'method SetTipTouch'
		return self._oleobj_.InvokeTypes(26, LCID, 1, (3, 0), ((2, 0), (5, 0), (5, 0)),NumberOfSides
			, RetractDistance, HorizontalOffset)

	def Shake(self, PlateLocation=defaultNamedNotOptArg, Mode=defaultNamedNotOptArg, Speed=defaultNamedNotOptArg, Direction=defaultNamedNotOptArg
			, TimerInSeconds=defaultNamedNotOptArg):
		'Starts the Teleshake accessory task'
		return self._oleobj_.InvokeTypes(39, LCID, 1, (3, 0), ((2, 0), (2, 0), (2, 0), (2, 0), (5, 0)),PlateLocation
			, Mode, Speed, Direction, TimerInSeconds)

	def ShowDiagsDialog(self, modal=defaultNamedNotOptArg, securityLevel=defaultNamedNotOptArg):
		'Displays the device diagnostics'
		return self._oleobj_.InvokeTypes(9, LCID, 1, (24, 0), ((11, 0), (2, 0)),modal
			, securityLevel)

	def ShowLabwareEditor(self, VisibilityMask=defaultNamedNotOptArg):
		'Displays the Labware Editor with the appropriate tabs available to the user'
		return self._oleobj_.InvokeTypes(31, LCID, 1, (3, 0), ((3, 0),),VisibilityMask
			)

	def ShowLiquidLibraryEditor(self):
		'Displays the Liquid Library Editor'
		return self._oleobj_.InvokeTypes(32, LCID, 1, (3, 0), (),)

	def TipsOff(self, PlateLocation=defaultNamedNotOptArg):
		'Strips tips'
		return self._oleobj_.InvokeTypes(19, LCID, 1, (3, 0), ((2, 0),),PlateLocation
			)

	def TipsOn(self, PlateLocation=defaultNamedNotOptArg):
		'Presses tips on'
		return self._oleobj_.InvokeTypes(18, LCID, 1, (3, 0), ((2, 0),),PlateLocation
			)

	def VacuumFiltration(self, PlateLocation=defaultNamedNotOptArg, Mode=defaultNamedNotOptArg, TimerInSeconds=defaultNamedNotOptArg):
		'Starts the Vacuum Filtration task'
		return self._oleobj_.InvokeTypes(40, LCID, 1, (3, 0), ((2, 0), (2, 0), (5, 0)),PlateLocation
			, Mode, TimerInSeconds)

	def WaitForUser(self, WaitForGoMessage=defaultNamedNotOptArg):
		'Waits for the user to press the silver Go button'
		return self._oleobj_.InvokeTypes(21, LCID, 1, (3, 0), ((8, 0),),WaitForGoMessage
			)

	def Wash(self, Volume=defaultNamedNotOptArg, EmptyTips=defaultNamedNotOptArg, PreAspirateVolume=defaultNamedNotOptArg, BlowoutVolume=defaultNamedNotOptArg
			, Cycles=defaultNamedNotOptArg, PlateLocation=defaultNamedNotOptArg, DistanceFromWellBottom=defaultNamedNotOptArg, RetractDistancePerMicroliter=defaultNamedNotOptArg, PumpInflowSpeed=defaultNamedNotOptArg
			, PumpOutflowSpeed=defaultNamedNotOptArg):
		'Washes tips'
		return self._oleobj_.InvokeTypes(17, LCID, 1, (3, 0), ((5, 0), (11, 0), (5, 0), (5, 0), (2, 0), (2, 0), (5, 0), (5, 0), (5, 0), (5, 0)),Volume
			, EmptyTips, PreAspirateVolume, BlowoutVolume, Cycles, PlateLocation
			, DistanceFromWellBottom, RetractDistancePerMicroliter, PumpInflowSpeed, PumpOutflowSpeed)

	_prop_map_get_ = {
		"Blocking": (2, 2, (11, 0), (), "Blocking", None),
		# Property 'ControlPicture' is an object of type 'Picture'
		"ControlPicture": (1, 2, (9, 0), (), "ControlPicture", '{7BF80981-BF32-101A-8BBB-00AA00300CAB}'),
		# Property 'GetDeckLayoutGraphic' is an object of type 'Picture'
		"GetDeckLayoutGraphic": (38, 2, (9, 0), (), "GetDeckLayoutGraphic", '{7BF80981-BF32-101A-8BBB-00AA00300CAB}'),
	}
	_prop_map_put_ = {
		"Blocking" : ((2, LCID, 4, 0),()),
		"ControlPicture" : ((1, LCID, 4, 0),()),
		"GetDeckLayoutGraphic" : ((38, LCID, 4, 0),()),
	}
	def __iter__(self):
		"Return a Python iterator for this object"
		try:
			ob = self._oleobj_.InvokeTypes(-4,LCID,3,(13, 10),())
		except pythoncom.error:
			raise TypeError("This object does not support enumeration")
		return win32com.client.util.Iterator(ob, None)

class _DHomewoodEvents:
	'Event interface for Homewood Control'
	CLSID = CLSID_Sink = IID('{0CA60D1B-792B-404D-A45F-3046B9BDDED4}')
	coclass_clsid = IID('{C912FE20-06A6-4B7C-9BFB-F7B3EE29092E}')
	_public_methods_ = [] # For COM Server support
	_dispid_to_func_ = {
		     -608 : "OnError",
		        1 : "OnInitializeComplete",
		        2 : "OnCloseComplete",
		        3 : "OnAspirateComplete",
		        4 : "OnDispenseComplete",
		        5 : "OnMixComplete",
		        6 : "OnWashComplete",
		        7 : "OnTipsOnComplete",
		        8 : "OnTipsOffComplete",
		        9 : "OnPumpReagentComplete",
		       10 : "OnWaitForUserComplete",
		       11 : "OnMoveToLocationComplete",
		       12 : "OnPickAndPlaceComplete",
		       13 : "OnMoveToPositionComplete",
		       14 : "OnShakeComplete",
		       15 : "OnVacuumFiltrationComplete",
		       16 : "OnLiddingOperationComplete",
		       17 : "OnVacuumAssemblyComplete",
		}

	def __init__(self, oobj = None):
		if oobj is None:
			self._olecp = None
		else:
			import win32com.server.util
			from win32com.server.policy import EventHandlerPolicy
			cpc=oobj._oleobj_.QueryInterface(pythoncom.IID_IConnectionPointContainer)
			cp=cpc.FindConnectionPoint(self.CLSID_Sink)
			cookie=cp.Advise(win32com.server.util.wrap(self, usePolicy=EventHandlerPolicy))
			self._olecp,self._olecp_cookie = cp,cookie
	def __del__(self):
		try:
			self.close()
		except pythoncom.com_error:
			pass
	def close(self):
		if self._olecp is not None:
			cp,cookie,self._olecp,self._olecp_cookie = self._olecp,self._olecp_cookie,None,None
			cp.Unadvise(cookie)
	def _query_interface_(self, iid):
		import win32com.server.util
		if iid==self.CLSID_Sink: return win32com.server.util.wrap(self)

	# Event Handlers
	# If you create handlers, they should have the following prototypes:
#	def OnError(self, Number=defaultNamedNotOptArg, Description=defaultNamedNotOptArg, Scode=defaultNamedNotOptArg, Source=defaultNamedNotOptArg
#			, HelpFile=defaultNamedNotOptArg, HelpContext=defaultNamedNotOptArg, CancelDisplay=defaultNamedNotOptArg):
#	def OnInitializeComplete(self):
#	def OnCloseComplete(self):
#	def OnAspirateComplete(self):
#	def OnDispenseComplete(self):
#	def OnMixComplete(self):
#	def OnWashComplete(self):
#	def OnTipsOnComplete(self):
#	def OnTipsOffComplete(self):
#	def OnPumpReagentComplete(self):
#	def OnWaitForUserComplete(self):
#	def OnMoveToLocationComplete(self):
#	def OnPickAndPlaceComplete(self):
#	def OnMoveToPositionComplete(self):
#	def OnShakeComplete(self):
#	def OnVacuumFiltrationComplete(self):
#	def OnLiddingOperationComplete(self):
#	def OnVacuumAssemblyComplete(self):


from win32com.client import CoClassBaseClass
# This CoClass is known by the name 'HW.HomewoodCtrl.1'
class Homewood(CoClassBaseClass): # A CoClass
	# Homewood Control
	CLSID = IID('{C912FE20-06A6-4B7C-9BFB-F7B3EE29092E}')
	coclass_sources = [
		_DHomewoodEvents,
	]
	default_source = _DHomewoodEvents
	coclass_interfaces = [
		_DHomewood,
	]
	default_interface = _DHomewood

# This CoClass is known by the name 'Homewood.HomewoodDriver.1'
class HomewoodDriver(CoClassBaseClass): # A CoClass
	# HomewoodDriver Class
	CLSID = IID('{E45DA461-72C7-447F-BB44-5BAF96A61353}')
	coclass_sources = [
	]
	coclass_interfaces = [
	]

IHomewoodDriver_vtables_dispatch_ = 0
IHomewoodDriver_vtables_ = [
]

RecordMap = {
}

CLSIDToClassMap = {
	'{18C9D060-CD66-4A19-84DE-FD472156A79B}' : _DHomewood,
	'{0CA60D1B-792B-404D-A45F-3046B9BDDED4}' : _DHomewoodEvents,
	'{C912FE20-06A6-4B7C-9BFB-F7B3EE29092E}' : Homewood,
	'{E45DA461-72C7-447F-BB44-5BAF96A61353}' : HomewoodDriver,
}
CLSIDToPackageMap = {}
win32com.client.CLSIDToClass.RegisterCLSIDsFromDict( CLSIDToClassMap )
VTablesToPackageMap = {}
VTablesToClassMap = {
	'{EADDB17A-80F8-4CF7-A6AE-D60939B4BB6B}' : 'IHomewoodDriver',
}


NamesToIIDMap = {
	'_DHomewood' : '{18C9D060-CD66-4A19-84DE-FD472156A79B}',
	'_DHomewoodEvents' : '{0CA60D1B-792B-404D-A45F-3046B9BDDED4}',
	'IHomewoodDriver' : '{EADDB17A-80F8-4CF7-A6AE-D60939B4BB6B}',
}


