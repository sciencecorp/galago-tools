# -*- coding: utf-8 -*-
# Created by makepy.py version 0.5.01
# By python version 3.10.4 | packaged by conda-forge | (main, Mar 30 2022, 08:38:02) [MSC v.1916 64 bit (AMD64)]
# From type library 'Gen5.exe'
# On Thu Aug 17 16:26:05 2023
''
makepy_version = '0.5.01'
python_version = 0x30a04f0

import win32com.client.CLSIDToClass, pythoncom, pywintypes
import win32com.client.util
from pywintypes import IID
from win32com.client import Dispatch

# The following 3 lines may need tweaking for the particular server
# Candidates are pythoncom.Missing, .Empty and .ArgNotFound
defaultNamedOptArg=pythoncom.Empty
defaultNamedNotOptArg=pythoncom.Empty
defaultUnnamedArg=pythoncom.Empty

CLSID = IID('{80BC3D0F-EA45-49B3-8F79-4E0B1D635711}')
MajorVersion = 1
MinorVersion = 0
LibraryFlags = 8
LCID = 0x0

class constants:
	eCalculationCompleted         =3          # from enum Gen5CalculationStatus
	eCalculationNotStarted        =0          # from enum Gen5CalculationStatus
	eCalculationPaused            =2          # from enum Gen5CalculationStatus
	eCalculationRunning           =1          # from enum Gen5CalculationStatus
	eCalculationStatusUnknown     =-1         # from enum Gen5CalculationStatus
	eOLECommunication             =1          # from enum Gen5CommunicationType
	eSerialCommunication          =0          # from enum Gen5CommunicationType
	eFileTypeExp                  =1          # from enum Gen5FileType
	eFileTypeOpn                  =4          # from enum Gen5FileType
	eFileTypePnl                  =8          # from enum Gen5FileType
	eFileTypePrt                  =2          # from enum Gen5FileType
	eFileTypeXts                  =16         # from enum Gen5FileType
	eRawDataFoundWithMore         =1          # from enum Gen5GetRawDataStatus
	eRawDataFoundWithNoMore       =2          # from enum Gen5GetRawDataStatus
	eRawDataNoneAvailable         =0          # from enum Gen5GetRawDataStatus
	eFromProtocolFile             =0          # from enum Gen5NewExperimentMode
	eFromProtocolMetadata         =1          # from enum Gen5NewExperimentMode
	ePlateTypeCalibration         =1          # from enum Gen5PlateType
	ePlateTypeStandard            =0          # from enum Gen5PlateType
	ePlateTypeSelectionFavorite   =1          # from enum Gen5PlateTypeSelection
	ePlateTypeSelectionHasLid     =8          # from enum Gen5PlateTypeSelection
	ePlateTypeSelectionTypeCustom =4          # from enum Gen5PlateTypeSelection
	ePlateTypeSelectionTypeDefault=2          # from enum Gen5PlateTypeSelection
	eWellStatusError              =4          # from enum Gen5PrimaryWellStatus
	eWellStatusMasked             =3          # from enum Gen5PrimaryWellStatus
	eWellStatusMissedValue        =2          # from enum Gen5PrimaryWellStatus
	eWellStatusNoValue            =5          # from enum Gen5PrimaryWellStatus
	eWellStatusOK                 =0          # from enum Gen5PrimaryWellStatus
	eWellStatusOutOfRange         =1          # from enum Gen5PrimaryWellStatus
	eProtocolTypeCalibration      =1          # from enum Gen5ProtocolType
	eProtocolTypeMultiPlateAssay  =2          # from enum Gen5ProtocolType
	eProtocolTypeStandard         =0          # from enum Gen5ProtocolType
	eReadAborted                  =2          # from enum Gen5ReadStatus
	eReadCompleted                =5          # from enum Gen5ReadStatus
	eReadError                    =4          # from enum Gen5ReadStatus
	eReadInProgress               =1          # from enum Gen5ReadStatus
	eReadNotStarted               =0          # from enum Gen5ReadStatus
	eReadPaused                   =3          # from enum Gen5ReadStatus
	eAbsorbanceReadModeCount      =3          # from enum Gen5ReaderCharacteristicsID
	eAbsorbanceReadModeName       =4          # from enum Gen5ReaderCharacteristicsID
	eAbsorbanceReadSuported       =0          # from enum Gen5ReaderCharacteristicsID
	eAbsorbanceWavelengthMax      =2          # from enum Gen5ReaderCharacteristicsID
	eAbsorbanceWavelengthMin      =1          # from enum Gen5ReaderCharacteristicsID
	eFilterFluorescenceSupported  =12         # from enum Gen5ReaderCharacteristicsID
	eInstrumentName               =11         # from enum Gen5ReaderCharacteristicsID
	eMonoFluorescenceSupported    =13         # from enum Gen5ReaderCharacteristicsID
	eReaderArchitectureLevel      =14         # from enum Gen5ReaderCharacteristicsID
	eSerialNumber                 =10         # from enum Gen5ReaderCharacteristicsID
	eShakeSupported               =9          # from enum Gen5ReaderCharacteristicsID
	eTemperatureControlOption     =5          # from enum Gen5ReaderCharacteristicsID
	eTemperatureGradientMax       =8          # from enum Gen5ReaderCharacteristicsID
	eTemperatureMax               =7          # from enum Gen5ReaderCharacteristicsID
	eTemperatureMin               =6          # from enum Gen5ReaderCharacteristicsID
	eReaderCommand_CleanObjective =2048       # from enum Gen5ReaderControlCommand
	eReaderCommand_ControlDispenser=8          # from enum Gen5ReaderControlCommand
	eReaderCommand_ControlDoor    =2          # from enum Gen5ReaderControlCommand
	eReaderCommand_ControlGasCharge=128        # from enum Gen5ReaderControlCommand
	eReaderCommand_ControlIncubator=16         # from enum Gen5ReaderControlCommand
	eReaderCommand_ControlLamp    =32         # from enum Gen5ReaderControlCommand
	eReaderCommand_ControlPrime   =64         # from enum Gen5ReaderControlCommand
	eReaderCommand_ControlShake   =4          # from enum Gen5ReaderControlCommand
	eReaderCommand_DoorIn         =512        # from enum Gen5ReaderControlCommand
	eReaderCommand_DoorOut        =1024       # from enum Gen5ReaderControlCommand
	eReaderCommand_ShowControlPanel=0          # from enum Gen5ReaderControlCommand
	eReaderCommand_ShowInformation=1          # from enum Gen5ReaderControlCommand
	eReaderStatus_Busy            =-1         # from enum Gen5ReaderStatus
	eReaderStatus_NotCommunicating=-2         # from enum Gen5ReaderStatus
	eReaderStatus_NotConfigured   =-3         # from enum Gen5ReaderStatus
	eReaderStatus_OK              =0          # from enum Gen5ReaderStatus
	eSecondaryStatusInjector1     =1          # from enum Gen5SecondaryWellStatus
	eSecondaryStatusInjector2     =2          # from enum Gen5SecondaryWellStatus
	eSecondaryStatusInjector3     =3          # from enum Gen5SecondaryWellStatus
	eSecondaryStatusInjector4     =4          # from enum Gen5SecondaryWellStatus
	eSecondaryStatusOK            =0          # from enum Gen5SecondaryWellStatus
	eTemperatureDirectFromReader  =1          # from enum Gen5TemperatureStatus
	eTemperatureInValid           =-2         # from enum Gen5TemperatureStatus
	eTemperatureNotInitialized    =-1         # from enum Gen5TemperatureStatus
	eTemperatureNotSupported      =-3         # from enum Gen5TemperatureStatus
	eTemperatureObtainedWithReaderData=2          # from enum Gen5TemperatureStatus

from win32com.client import DispatchBaseClass
class IApplication(DispatchBaseClass):
	CLSID = IID('{56BBF0D8-DDE6-4F25-BEE1-F3A7CC516531}')
	coclass_clsid = IID('{9B3B05F7-143C-4DAF-93D8-726A7BA3321A}')

	def BrowseForFile(self, OpenFileDlg=defaultNamedNotOptArg, FileName=defaultNamedNotOptArg, DialogTitle=defaultNamedNotOptArg, eFileType=defaultNamedNotOptArg):
		'method BrowseForFile'
		# Result is a Unicode object
		return self._oleobj_.InvokeTypes(11, LCID, 1, (8, 0), ((11, 0), (8, 0), (8, 0), (3, 0)),OpenFileDlg
			, FileName, DialogTitle, eFileType)

	def BrowseForFolder(self, FolderName=defaultNamedNotOptArg):
		'method BrowseForFolder'
		# Result is a Unicode object
		return self._oleobj_.InvokeTypes(12, LCID, 1, (8, 0), ((8, 0),),FolderName
			)

	def CarrierIn(self):
		'method CarrierIn'
		return self._oleobj_.InvokeTypes(13, LCID, 1, (24, 0), (),)

	def CarrierInEx(self, p_pszPlateTypeName=defaultNamedNotOptArg, p_bLidOnPlate=defaultNamedNotOptArg):
		'method CarrierInEx'
		return self._oleobj_.InvokeTypes(37, LCID, 1, (24, 0), ((8, 0), (11, 0)),p_pszPlateTypeName
			, p_bLidOnPlate)

	def CarrierOut(self):
		'method CarrierOut'
		return self._oleobj_.InvokeTypes(14, LCID, 1, (24, 0), (),)

	def ClearTipPrimeTrough(self):
		'method ClearTipPrimeTrough'
		return self._oleobj_.InvokeTypes(25, LCID, 1, (24, 0), (),)

	def ConfigureOleReader(self, ReaderType=defaultNamedNotOptArg):
		'method ConfigureOleReader'
		return self._oleobj_.InvokeTypes(8, LCID, 1, (24, 0), ((3, 0),),ReaderType
			)

	def ConfigureSerialReader(self, ReaderType=defaultNamedNotOptArg, ComPort=defaultNamedNotOptArg, BaudRate=defaultNamedNotOptArg):
		'method ConfigureSerialReader'
		return self._oleobj_.InvokeTypes(9, LCID, 1, (24, 0), ((3, 0), (3, 0), (3, 0)),ReaderType
			, ComPort, BaudRate)

	def ConfigureUSBReader(self, ReaderType=defaultNamedNotOptArg, ReaderSN=defaultNamedNotOptArg):
		'method ConfigureUSBReader'
		return self._oleobj_.InvokeTypes(23, LCID, 1, (24, 0), ((3, 0), (8, 0)),ReaderType
			, ReaderSN)

	def DiagTestPlateRunDlg(self):
		'method DiagTestPlateRunDlg'
		return self._oleobj_.InvokeTypes(45, LCID, 1, (24, 0), (),)

	def DisplayAbsorbanceTestPlateDlg(self):
		'method DisplayAbsorbanceTestPlateDlg'
		return self._oleobj_.InvokeTypes(44, LCID, 1, (24, 0), (),)

	def DisplayImagingLiveModeDialog(self):
		'method DisplayImagingLiveModeDialog'
		return self._oleobj_.InvokeTypes(41, LCID, 1, (24, 0), (),)

	def EditPlateTypes(self):
		'method EditPlateTypes'
		return self._oleobj_.InvokeTypes(29, LCID, 1, (24, 0), (),)

	def GetBioStackInterfaceID(self, ReaderType=defaultNamedNotOptArg):
		'method GetBioStackInterfaceID'
		return self._oleobj_.InvokeTypes(20, LCID, 1, (3, 0), ((3, 0),),ReaderType
			)

	def GetConfiguredInstruments(self):
		'method GetConfiguredInstruments'
		# Result is a Unicode object
		return self._oleobj_.InvokeTypes(39, LCID, 1, (8, 0), (),)

	def GetCurrentTemperature(self, pvTemperatureValue=defaultNamedNotOptArg, pnTemperatureStatus=defaultNamedNotOptArg):
		'method GetCurrentTemperature'
		return self._oleobj_.InvokeTypes(26, LCID, 1, (24, 0), ((16396, 0), (16396, 0)),pvTemperatureValue
			, pnTemperatureStatus)

	def GetCurrentTemperatureFP(self, pvTemperatureValue=defaultNamedNotOptArg, pnTemperatureStatus=defaultNamedNotOptArg):
		'method GetCurrentTemperatureFP'
		return self._oleobj_.InvokeTypes(42, LCID, 1, (24, 0), ((16396, 0), (16396, 0)),pvTemperatureValue
			, pnTemperatureStatus)

	def GetHotelInterfaceID(self, ReaderType=defaultNamedNotOptArg):
		'method GetHotelInterfaceID'
		return self._oleobj_.InvokeTypes(30, LCID, 1, (3, 0), ((3, 0),),ReaderType
			)

	def GetLastReaderError(self):
		'method GetLastReaderError'
		return self._oleobj_.InvokeTypes(15, LCID, 1, (3, 0), (),)

	def GetMonoCalTestResults(self, pvPeakWavelength=defaultNamedNotOptArg, pvError=defaultNamedNotOptArg):
		'method GetMonoCalTestResults'
		return self._oleobj_.InvokeTypes(22, LCID, 1, (3, 0), ((16396, 0), (16396, 0)),pvPeakWavelength
			, pvError)

	def GetPlateTypeDefinition(self, p_strName=defaultNamedNotOptArg):
		'method GetPlateTypeDefinition'
		# Result is a Unicode object
		return self._oleobj_.InvokeTypes(27, LCID, 1, (8, 0), ((8, 0),),p_strName
			)

	def GetPlateTypeNames(self, p_nSelectionFlag=defaultNamedNotOptArg, pvNames=defaultNamedNotOptArg):
		'method GetPlateTypeNames'
		return self._oleobj_.InvokeTypes(28, LCID, 1, (24, 0), ((2, 0), (16396, 0)),p_nSelectionFlag
			, pvNames)

	def GetReaderCharacteristics(self, ReaderCharacteristicsID=defaultNamedNotOptArg, ReaderCharacteristicsIndex=defaultNamedNotOptArg, pvValue=defaultNamedNotOptArg):
		'method GetReaderCharacteristics'
		return self._oleobj_.InvokeTypes(35, LCID, 1, (24, 0), ((3, 0), (3, 0), (16396, 0)),ReaderCharacteristicsID
			, ReaderCharacteristicsIndex, pvValue)

	def GetReaderStatus(self):
		'method GetReaderStatus'
		return self._oleobj_.InvokeTypes(34, LCID, 1, (3, 0), (),)

	def GetSupportedReaders(self, pvReaderName=defaultNamedNotOptArg, pvReaderType=defaultNamedNotOptArg, pvCommunicationType=defaultNamedNotOptArg):
		'method GetSupportedReaders'
		return self._oleobj_.InvokeTypes(19, LCID, 1, (24, 0), ((16396, 0), (16396, 0), (16396, 0)),pvReaderName
			, pvReaderType, pvCommunicationType)

	def GetTemperatureSetPoint(self, pvSetpoint=defaultNamedNotOptArg, pvGradient=defaultNamedNotOptArg):
		'method GetTemperatureSetPoint'
		return self._oleobj_.InvokeTypes(36, LCID, 1, (24, 0), ((16396, 0), (16396, 0)),pvSetpoint
			, pvGradient)

	def ImportPlateTypeDefinition(self, p_strImportPlateTypeXML=defaultNamedNotOptArg):
		'method ImportPlateTypeDefinition'
		return self._oleobj_.InvokeTypes(40, LCID, 1, (24, 0), ((8, 0),),p_strImportPlateTypeXML
			)

	def NewExperiment(self, ProtocolPathName=defaultNamedNotOptArg):
		'method NewExperiment'
		ret = self._oleobj_.InvokeTypes(6, LCID, 1, (9, 0), ((8, 0),),ProtocolPathName
			)
		if ret is not None:
			ret = Dispatch(ret, 'NewExperiment', None)
		return ret

	def NewExperimentEx(self, CreationMode=defaultNamedNotOptArg, ProtocolMetadata=defaultNamedNotOptArg):
		'method NewExperimentEx'
		ret = self._oleobj_.InvokeTypes(33, LCID, 1, (9, 0), ((3, 0), (8, 0)),CreationMode
			, ProtocolMetadata)
		if ret is not None:
			ret = Dispatch(ret, 'NewExperimentEx', None)
		return ret

	def OpenClinicalDatabaseGroup(self, DatabasePathname=defaultNamedNotOptArg, Group=defaultNamedNotOptArg, UseQCRTool=defaultNamedNotOptArg):
		'method OpenClinicalDatabaseGroup'
		return self._oleobj_.InvokeTypes(17, LCID, 1, (24, 0), ((8, 0), (8, 0), (11, 0)),DatabasePathname
			, Group, UseQCRTool)

	def OpenExperiment(self, PathName=defaultNamedNotOptArg):
		'method OpenExperiment'
		ret = self._oleobj_.InvokeTypes(7, LCID, 1, (9, 0), ((8, 0),),PathName
			)
		if ret is not None:
			ret = Dispatch(ret, 'OpenExperiment', None)
		return ret

	def RunReaderControlCommand(self, p_nCommand=defaultNamedNotOptArg):
		'method RunReaderControlCommand'
		return self._oleobj_.InvokeTypes(31, LCID, 1, (24, 0), ((3, 0),),p_nCommand
			)

	def SetClientWindow(self, ClientWindowHandle=defaultNamedNotOptArg):
		'method SetClientWindow'
		return self._oleobj_.InvokeTypes(10, LCID, 1, (24, 0), ((3, 0),),ClientWindowHandle
			)

	def SetTemperatureSetPoint(self, p_bIncubatorState=defaultNamedNotOptArg, p_nTemperatureSetPoint=defaultNamedNotOptArg, p_nGradient=defaultNamedNotOptArg):
		'method SetTemperatureSetPoint'
		return self._oleobj_.InvokeTypes(32, LCID, 1, (24, 0), ((11, 0), (2, 0), (2, 0)),p_bIncubatorState
			, p_nTemperatureSetPoint, p_nGradient)

	def SimpleRequestResponseHandler(self, p_chCommand=defaultNamedNotOptArg, p_byCommandBody=defaultNamedNotOptArg, p_nCommandBodyLength=defaultNamedNotOptArg, p_pbyResponseStream=defaultNamedNotOptArg
			, p_nExpectedResponseLength=defaultNamedNotOptArg, p_lMSecTimeoutValue=defaultNamedNotOptArg, p_plReaderHexError=defaultNamedNotOptArg):
		'method SimpleRequestResponseHandler'
		return self._oleobj_.InvokeTypes(43, LCID, 1, (2, 0), ((8, 0), (8, 0), (2, 0), (16392, 0), (2, 0), (3, 0), (16387, 0)),p_chCommand
			, p_byCommandBody, p_nCommandBodyLength, p_pbyResponseStream, p_nExpectedResponseLength, p_lMSecTimeoutValue
			, p_plReaderHexError)

	def StartMonoCalTest(self, PathName=defaultNamedNotOptArg):
		'method StartMonoCalTest'
		ret = self._oleobj_.InvokeTypes(21, LCID, 1, (9, 0), ((8, 0),),PathName
			)
		if ret is not None:
			ret = Dispatch(ret, 'StartMonoCalTest', None)
		return ret

	def StartSystemTest(self, p_bForceNewSystemTest=defaultNamedNotOptArg):
		'method StartSystemTest'
		ret = self._oleobj_.InvokeTypes(38, LCID, 1, (9, 0), ((11, 0),),p_bForceNewSystemTest
			)
		if ret is not None:
			ret = Dispatch(ret, 'StartSystemTest', None)
		return ret

	def TestReaderCommunication(self):
		'method TestReaderCommunication'
		return self._oleobj_.InvokeTypes(16, LCID, 1, (3, 0), (),)

	_prop_map_get_ = {
		"AllowInterruptedDiscontinuousKineticResume": (46, 2, (11, 0), (), "AllowInterruptedDiscontinuousKineticResume", None),
		"CreateTempFileIfUnsavedExperiment": (24, 2, (11, 0), (), "CreateTempFileIfUnsavedExperiment", None),
		"DataExportEnabled": (18, 2, (11, 0), (), "DataExportEnabled", None),
		"DatabaseFileStorage": (5, 2, (11, 0), (), "DatabaseFileStorage", None),
		"Gen5AppPath": (4, 2, (8, 0), (), "Gen5AppPath", None),
		"Gen5BuildNumber": (3, 2, (3, 0), (), "Gen5BuildNumber", None),
		"Gen5VersionNumber": (2, 2, (5, 0), (), "Gen5VersionNumber", None),
		"Gen5VersionString": (1, 2, (8, 0), (), "Gen5VersionString", None),
	}
	_prop_map_put_ = {
		"AllowInterruptedDiscontinuousKineticResume" : ((46, LCID, 4, 0),()),
		"CreateTempFileIfUnsavedExperiment" : ((24, LCID, 4, 0),()),
		"DataExportEnabled" : ((18, LCID, 4, 0),()),
		"DatabaseFileStorage" : ((5, LCID, 4, 0),()),
		"Gen5AppPath" : ((4, LCID, 4, 0),()),
		"Gen5BuildNumber" : ((3, LCID, 4, 0),()),
		"Gen5VersionNumber" : ((2, LCID, 4, 0),()),
		"Gen5VersionString" : ((1, LCID, 4, 0),()),
	}
	def __iter__(self):
		"Return a Python iterator for this object"
		try:
			ob = self._oleobj_.InvokeTypes(-4,LCID,3,(13, 10),())
		except pythoncom.error:
			raise TypeError("This object does not support enumeration")
		return win32com.client.util.Iterator(ob, None)

class IExperiment(DispatchBaseClass):
	CLSID = IID('{21258B83-0AAE-43F7-AFBC-89C680D51C6F}')
	coclass_clsid = IID('{F4024CA7-7362-4FC8-B33F-F1F2BD58788F}')

	def AddAuditTrailRecord(self, p_pszDescription=defaultNamedNotOptArg, p_pszComment=defaultNamedNotOptArg):
		'method AddAuditTrailRecord'
		return self._oleobj_.InvokeTypes(15, LCID, 1, (24, 0), ((8, 0), (8, 0)),p_pszDescription
			, p_pszComment)

	def Close(self):
		'method Close'
		return self._oleobj_.InvokeTypes(8, LCID, 1, (24, 0), (),)

	def GetPlateLayout(self, ProtocolID=defaultNamedNotOptArg):
		'method GetPlateLayout'
		# Result is a Unicode object
		return self._oleobj_.InvokeTypes(10, LCID, 1, (8, 0), ((8, 0),),ProtocolID
			)

	def GetSampleIdentification(self):
		'method GetSampleIdentification'
		# Result is a Unicode object
		return self._oleobj_.InvokeTypes(12, LCID, 1, (8, 0), (),)

	def Save(self):
		'method Save'
		return self._oleobj_.InvokeTypes(7, LCID, 1, (24, 0), (),)

	def SaveAs(self, PathName=defaultNamedNotOptArg):
		'method SaveAs'
		return self._oleobj_.InvokeTypes(9, LCID, 1, (24, 0), ((8, 0),),PathName
			)

	def SetPlateLayout(self, PlateLayoutXML=defaultNamedNotOptArg):
		'method SetPlateLayout'
		return self._oleobj_.InvokeTypes(11, LCID, 1, (24, 0), ((8, 0),),PlateLayoutXML
			)

	def SetSampleIdentification(self, SampleIdentificationXML=defaultNamedNotOptArg):
		'method SetSampleIdentification'
		return self._oleobj_.InvokeTypes(13, LCID, 1, (24, 0), ((8, 0),),SampleIdentificationXML
			)

	_prop_map_get_ = {
		"AutoFileExport": (4, 2, (11, 0), (), "AutoFileExport", None),
		"AutoPowerExport": (5, 2, (11, 0), (), "AutoPowerExport", None),
		"AutoPrintReport": (3, 2, (11, 0), (), "AutoPrintReport", None),
		"AutoSave": (2, 2, (11, 0), (), "AutoSave", None),
		"DeleteObsoleteDRFoldersOnSave": (14, 2, (11, 0), (), "DeleteObsoleteDRFoldersOnSave", None),
		"Plates": (1, 2, (9, 0), (), "Plates", None),
		"ProtocolType": (6, 2, (3, 0), (), "ProtocolType", None),
	}
	_prop_map_put_ = {
		"AutoFileExport" : ((4, LCID, 4, 0),()),
		"AutoPowerExport" : ((5, LCID, 4, 0),()),
		"AutoPrintReport" : ((3, LCID, 4, 0),()),
		"AutoSave" : ((2, LCID, 4, 0),()),
		"DeleteObsoleteDRFoldersOnSave" : ((14, LCID, 4, 0),()),
		"Plates" : ((1, LCID, 4, 0),()),
		"ProtocolType" : ((6, LCID, 4, 0),()),
	}
	def __iter__(self):
		"Return a Python iterator for this object"
		try:
			ob = self._oleobj_.InvokeTypes(-4,LCID,3,(13, 10),())
		except pythoncom.error:
			raise TypeError("This object does not support enumeration")
		return win32com.client.util.Iterator(ob, None)

class IMonoCalTestMonitor(DispatchBaseClass):
	CLSID = IID('{0DABEE12-4422-4FE2-8D4B-F510CA25ECD7}')
	coclass_clsid = IID('{9EFA02E9-6776-44B3-B193-62A360356658}')

	def GetErrorMessage(self):
		'method GetErrorMessage'
		# Result is a Unicode object
		return self._oleobj_.InvokeTypes(3, LCID, 1, (8, 0), (),)

	_prop_map_get_ = {
		"TestInProgress": (1, 2, (11, 0), (), "TestInProgress", None),
		"TestSuccessful": (2, 2, (11, 0), (), "TestSuccessful", None),
	}
	_prop_map_put_ = {
		"TestInProgress" : ((1, LCID, 4, 0),()),
		"TestSuccessful" : ((2, LCID, 4, 0),()),
	}
	def __iter__(self):
		"Return a Python iterator for this object"
		try:
			ob = self._oleobj_.InvokeTypes(-4,LCID,3,(13, 10),())
		except pythoncom.error:
			raise TypeError("This object does not support enumeration")
		return win32com.client.util.Iterator(ob, None)

class IPlate(DispatchBaseClass):
	CLSID = IID('{450BF0EA-F196-4D18-AD0D-DB39D2E6E08B}')
	coclass_clsid = IID('{DA2A9CC3-FE47-441B-BD0C-B482015A525F}')

	def AbortRead(self):
		'method AbortRead'
		return self._oleobj_.InvokeTypes(11, LCID, 1, (24, 0), (),)

	def AddAuditTrailRecord(self, p_pszDescription=defaultNamedNotOptArg, p_pszComment=defaultNamedNotOptArg):
		'method AddAuditTrailRecord'
		return self._oleobj_.InvokeTypes(69, LCID, 1, (24, 0), ((8, 0), (8, 0)),p_pszDescription
			, p_pszComment)

	def AsyncMovieExport(self, p_pszBuilderName=defaultNamedNotOptArg, p_pszFolderName=defaultNamedNotOptArg):
		'method AsyncMovieExport'
		ret = self._oleobj_.InvokeTypes(66, LCID, 1, (9, 0), ((8, 0), (8, 0)),p_pszBuilderName
			, p_pszFolderName)
		if ret is not None:
			ret = Dispatch(ret, 'AsyncMovieExport', None)
		return ret

	def AsyncPictureExport(self, p_pszBuilderName=defaultNamedNotOptArg, p_pszFolderName=defaultNamedNotOptArg):
		'method AsyncPictureExport'
		ret = self._oleobj_.InvokeTypes(65, LCID, 1, (9, 0), ((8, 0), (8, 0)),p_pszBuilderName
			, p_pszFolderName)
		if ret is not None:
			ret = Dispatch(ret, 'AsyncPictureExport', None)
		return ret

	def Delete(self):
		'method Delete'
		return self._oleobj_.InvokeTypes(14, LCID, 1, (24, 0), (),)

	def DisableKeepReadProcessGoingUntilCalculationsCompleted(self):
		'method DisableKeepReadProcessGoingUntilCalculationsCompleted'
		return self._oleobj_.InvokeTypes(55, LCID, 1, (24, 0), (),)

	def FileExport(self, ExportFilePath=defaultNamedNotOptArg):
		'method FileExport'
		return self._oleobj_.InvokeTypes(13, LCID, 1, (24, 0), ((8, 0),),ExportFilePath
			)

	def FileExportEx(self, p_pszBuilderName=defaultNamedNotOptArg, p_pszfilePath=defaultNamedNotOptArg):
		'method FileExportEx'
		return self._oleobj_.InvokeTypes(32, LCID, 1, (24, 0), ((8, 0), (8, 0)),p_pszBuilderName
			, p_pszfilePath)

	def GetChannelBCValues(self, ChannelName=defaultNamedNotOptArg, pBrightnessValue=defaultNamedNotOptArg, p_ContrastValue=defaultNamedNotOptArg):
		'method GetChannelBCValues'
		return self._oleobj_.InvokeTypes(61, LCID, 1, (24, 0), ((8, 0), (16396, 0), (16396, 0)),ChannelName
			, pBrightnessValue, p_ContrastValue)

	def GetDataReductionInfo(self, ProtocolID=defaultNamedNotOptArg):
		'method GetDataReductionInfo'
		# Result is a Unicode object
		return self._oleobj_.InvokeTypes(58, LCID, 1, (8, 0), ((8, 0),),ProtocolID
			)

	def GetDataSetInfo(self, pvDataSetName=defaultNamedNotOptArg, pvDecimalPlaces=defaultNamedNotOptArg, pvKineticReads=defaultNamedNotOptArg, pvKineticIntervalMSec=defaultNamedNotOptArg
			, pvDisplayMSec=defaultNamedNotOptArg, pvSpectrumWavelengths=defaultNamedNotOptArg, pvSpectrumStart=defaultNamedNotOptArg, pvSpectrumStep=defaultNamedNotOptArg, pvHorizontalReads=defaultNamedNotOptArg
			, pvVerticalReads=defaultNamedNotOptArg):
		'method GetDataSetInfo'
		return self._oleobj_.InvokeTypes(24, LCID, 1, (24, 0), ((16396, 0), (16396, 0), (16396, 0), (16396, 0), (16396, 0), (16396, 0), (16396, 0), (16396, 0), (16396, 0), (16396, 0)),pvDataSetName
			, pvDecimalPlaces, pvKineticReads, pvKineticIntervalMSec, pvDisplayMSec, pvSpectrumWavelengths
			, pvSpectrumStart, pvSpectrumStep, pvHorizontalReads, pvVerticalReads)

	def GetDataSetInfoEx(self, p_pszProtocolID=defaultNamedNotOptArg, p_pszDataSetName=defaultNamedNotOptArg):
		'method GetDataSetInfoEx'
		# Result is a Unicode object
		return self._oleobj_.InvokeTypes(49, LCID, 1, (8, 0), ((8, 0), (8, 0)),p_pszProtocolID
			, p_pszDataSetName)

	def GetDataSetNames(self, p_pszProtocolID=defaultNamedNotOptArg, pvNames=defaultNamedNotOptArg):
		'method GetDataSetNames'
		return self._oleobj_.InvokeTypes(48, LCID, 1, (24, 0), ((8, 0), (16396, 0)),p_pszProtocolID
			, pvNames)

	def GetDataSetROIsInWell(self, p_pszProtocolID=defaultNamedNotOptArg, p_pszDataSetName=defaultNamedNotOptArg, p_pszWellIndexes=defaultNamedNotOptArg):
		'method GetDataSetROIsInWell'
		return self._oleobj_.InvokeTypes(64, LCID, 1, (3, 0), ((8, 0), (8, 0), (8, 0)),p_pszProtocolID
			, p_pszDataSetName, p_pszWellIndexes)

	def GetDataSetResults(self, p_pszProtocolID=defaultNamedNotOptArg, p_pszDataSetName=defaultNamedNotOptArg, p_pszResultIndexes=defaultNamedNotOptArg):
		'method GetDataSetResults'
		# Result is a Unicode object
		return self._oleobj_.InvokeTypes(50, LCID, 1, (8, 0), ((8, 0), (8, 0), (8, 0)),p_pszProtocolID
			, p_pszDataSetName, p_pszResultIndexes)

	def GetFileExportNames(self, AutoExecuteOnly=defaultNamedNotOptArg, pvNames=defaultNamedNotOptArg):
		'method GetFileExportNames'
		return self._oleobj_.InvokeTypes(29, LCID, 1, (24, 0), ((11, 0), (16396, 0)),AutoExecuteOnly
			, pvNames)

	def GetImageFolderPaths(self, pvPaths=defaultNamedNotOptArg):
		'method GetImageFolderPaths'
		return self._oleobj_.InvokeTypes(40, LCID, 1, (24, 0), ((16396, 0),),pvPaths
			)

	def GetModifiableProcedure(self):
		'method GetModifiableProcedure'
		# Result is a Unicode object
		return self._oleobj_.InvokeTypes(56, LCID, 1, (8, 0), (),)

	def GetMovieExportNames(self, AutoExecuteOnly=defaultNamedNotOptArg, pvNames=defaultNamedNotOptArg):
		'method GetMovieExportNames'
		return self._oleobj_.InvokeTypes(42, LCID, 1, (24, 0), ((11, 0), (16396, 0)),AutoExecuteOnly
			, pvNames)

	def GetOLEMetaData(self, pvMetaData=defaultNamedNotOptArg):
		'method GetOLEMetaData'
		return self._oleobj_.InvokeTypes(67, LCID, 1, (24, 0), ((16396, 0),),pvMetaData
			)

	def GetPictureExportNames(self, AutoExecuteOnly=defaultNamedNotOptArg, pvNames=defaultNamedNotOptArg):
		'method GetPictureExportNames'
		return self._oleobj_.InvokeTypes(41, LCID, 1, (24, 0), ((11, 0), (16396, 0)),AutoExecuteOnly
			, pvNames)

	def GetPowerExportNames(self, AutoExecuteOnly=defaultNamedNotOptArg, pvNames=defaultNamedNotOptArg):
		'method GetPowerExportNames'
		return self._oleobj_.InvokeTypes(30, LCID, 1, (24, 0), ((11, 0), (16396, 0)),AutoExecuteOnly
			, pvNames)

	def GetProcedure(self):
		'method GetProcedure'
		# Result is a Unicode object
		return self._oleobj_.InvokeTypes(34, LCID, 1, (8, 0), (),)

	def GetRawData(self, pDataSetName=defaultNamedNotOptArg, pvRow=defaultNamedNotOptArg, pvColumn=defaultNamedNotOptArg, pvKineticIndex=defaultNamedNotOptArg
			, pvWavelengthIndex=defaultNamedNotOptArg, pvHorizontalIndex=defaultNamedNotOptArg, pvVerticalIndex=defaultNamedNotOptArg, pvValue=defaultNamedNotOptArg, pvPrimaryStatus=defaultNamedNotOptArg
			, pvSecondaryStatus=defaultNamedNotOptArg):
		'method GetRawData'
		return self._oleobj_.InvokeTypes(25, LCID, 1, (3, 0), ((16392, 0), (16396, 0), (16396, 0), (16396, 0), (16396, 0), (16396, 0), (16396, 0), (16396, 0), (16396, 0), (16396, 0)),pDataSetName
			, pvRow, pvColumn, pvKineticIndex, pvWavelengthIndex, pvHorizontalIndex
			, pvVerticalIndex, pvValue, pvPrimaryStatus, pvSecondaryStatus)

	def GetReportNames(self, AutoExecuteOnly=defaultNamedNotOptArg, pvNames=defaultNamedNotOptArg):
		'method GetReportNames'
		return self._oleobj_.InvokeTypes(28, LCID, 1, (24, 0), ((11, 0), (16396, 0)),AutoExecuteOnly
			, pvNames)

	def GetSampleDescription(self):
		'method GetSampleDescription'
		# Result is a Unicode object
		return self._oleobj_.InvokeTypes(26, LCID, 1, (8, 0), (),)

	def ImportSampleIDs(self, ImportFilePath=defaultNamedNotOptArg):
		'method ImportSampleIDs'
		return self._oleobj_.InvokeTypes(16, LCID, 1, (24, 0), ((8, 0),),ImportFilePath
			)

	def KeepPlateInAfterRead(self):
		'method KeepPlateInAfterRead'
		return self._oleobj_.InvokeTypes(46, LCID, 1, (24, 0), (),)

	def MovieExport(self, p_pszBuilderName=defaultNamedNotOptArg):
		'method MovieExport'
		# Result is a Unicode object
		return self._oleobj_.InvokeTypes(44, LCID, 1, (8, 0), ((8, 0),),p_pszBuilderName
			)

	def PictureExport(self, p_pszBuilderName=defaultNamedNotOptArg):
		'method PictureExport'
		# Result is a Unicode object
		return self._oleobj_.InvokeTypes(43, LCID, 1, (8, 0), ((8, 0),),p_pszBuilderName
			)

	def PowerExport(self, ExportFilePath=defaultNamedNotOptArg):
		'method PowerExport'
		return self._oleobj_.InvokeTypes(12, LCID, 1, (24, 0), ((8, 0),),ExportFilePath
			)

	def PowerExportEx(self, p_pszBuilderName=defaultNamedNotOptArg, p_pszfilePath=defaultNamedNotOptArg):
		'method PowerExportEx'
		return self._oleobj_.InvokeTypes(33, LCID, 1, (24, 0), ((8, 0), (8, 0)),p_pszBuilderName
			, p_pszfilePath)

	def PrintReport(self, ShowPrintDlg=defaultNamedNotOptArg):
		'method PrintReport'
		return self._oleobj_.InvokeTypes(15, LCID, 1, (24, 0), ((11, 0),),ShowPrintDlg
			)

	def PrintReportEx(self, p_pszBuilderName=defaultNamedNotOptArg, bShowPrintDlg=defaultNamedNotOptArg):
		'method PrintReportEx'
		return self._oleobj_.InvokeTypes(31, LCID, 1, (24, 0), ((8, 0), (3, 0)),p_pszBuilderName
			, bShowPrintDlg)

	def QCExport(self):
		'method QCExport'
		return self._oleobj_.InvokeTypes(21, LCID, 1, (24, 0), (),)

	def ResumeRead(self):
		'method ResumeRead'
		ret = self._oleobj_.InvokeTypes(9, LCID, 1, (9, 0), (),)
		if ret is not None:
			ret = Dispatch(ret, 'ResumeRead', None)
		return ret

	def ResumeReadEx(self, p_bRotate180Deg=defaultNamedNotOptArg):
		'method ResumeReadEx'
		ret = self._oleobj_.InvokeTypes(37, LCID, 1, (9, 0), ((11, 0),),p_bRotate180Deg
			)
		if ret is not None:
			ret = Dispatch(ret, 'ResumeReadEx', None)
		return ret

	def ResumeSimulatedRead(self):
		'method ResumeSimulatedRead'
		ret = self._oleobj_.InvokeTypes(10, LCID, 1, (9, 0), (),)
		if ret is not None:
			ret = Dispatch(ret, 'ResumeSimulatedRead', None)
		return ret

	def SetChannelBCValues(self, ChannelName=defaultNamedNotOptArg, BrightnessValue=defaultNamedNotOptArg, ContrastValue=defaultNamedNotOptArg):
		'method SetChannelBCValues'
		return self._oleobj_.InvokeTypes(62, LCID, 1, (24, 0), ((8, 0), (3, 0), (3, 0)),ChannelName
			, BrightnessValue, ContrastValue)

	def SetDataMaskedState(self, MaskRequestsXML=defaultNamedNotOptArg):
		'method SetDataMaskedState'
		return self._oleobj_.InvokeTypes(60, LCID, 1, (24, 0), ((8, 0),),MaskRequestsXML
			)

	def SetModifiableDataReduction(self, ProtocolID=defaultNamedNotOptArg, ModifiableDataReductionXML=defaultNamedNotOptArg):
		'method SetModifiableDataReduction'
		return self._oleobj_.InvokeTypes(59, LCID, 1, (24, 0), ((8, 0), (8, 0)),ProtocolID
			, ModifiableDataReductionXML)

	def SetModifiableProcedure(self, ModifiableProcedureXML=defaultNamedNotOptArg):
		'method SetModifiableProcedure'
		return self._oleobj_.InvokeTypes(57, LCID, 1, (24, 0), ((8, 0),),ModifiableProcedureXML
			)

	def SetOLEMetaData(self, pvMetaData=defaultNamedNotOptArg):
		'method SetOLEMetaData'
		return self._oleobj_.InvokeTypes(68, LCID, 1, (24, 0), ((16396, 0),),pvMetaData
			)

	def SetPartialPlate(self, p_pszPartialPlateXML=defaultNamedNotOptArg):
		'method SetPartialPlate'
		return self._oleobj_.InvokeTypes(45, LCID, 1, (24, 0), ((8, 0),),p_pszPartialPlateXML
			)

	def SetProcedure(self, ProcedureXML=defaultNamedNotOptArg):
		'method SetProcedure'
		return self._oleobj_.InvokeTypes(39, LCID, 1, (24, 0), ((8, 0),),ProcedureXML
			)

	def SetSampleDescription(self, SampleDescriptionXML=defaultNamedNotOptArg):
		'method SetSampleDescription'
		return self._oleobj_.InvokeTypes(27, LCID, 1, (24, 0), ((8, 0),),SampleDescriptionXML
			)

	def StartRead(self):
		'method StartRead'
		ret = self._oleobj_.InvokeTypes(6, LCID, 1, (9, 0), (),)
		if ret is not None:
			ret = Dispatch(ret, 'StartRead', None)
		return ret

	def StartReadEx(self, p_bRotate180Deg=defaultNamedNotOptArg):
		'method StartReadEx'
		ret = self._oleobj_.InvokeTypes(35, LCID, 1, (9, 0), ((11, 0),),p_bRotate180Deg
			)
		if ret is not None:
			ret = Dispatch(ret, 'StartReadEx', None)
		return ret

	def StartReadFromFile(self, FilePath=defaultNamedNotOptArg, ListSeparator=defaultNamedNotOptArg):
		'method StartReadFromFile'
		ret = self._oleobj_.InvokeTypes(8, LCID, 1, (9, 0), ((8, 0), (8, 0)),FilePath
			, ListSeparator)
		if ret is not None:
			ret = Dispatch(ret, 'StartReadFromFile', None)
		return ret

	def StartSimulatedRead(self):
		'method StartSimulatedRead'
		ret = self._oleobj_.InvokeTypes(7, LCID, 1, (9, 0), (),)
		if ret is not None:
			ret = Dispatch(ret, 'StartSimulatedRead', None)
		return ret

	def TryCellularAnalysisStep(self, CellularAnalysisStepXML=defaultNamedNotOptArg, ImageReferenceXML=defaultNamedNotOptArg, PictureExportBuilderName=defaultNamedNotOptArg, OutputPicturePathname=defaultNamedNotOptArg
			, p_ObjectCount=defaultNamedNotOptArg):
		'method TryCellularAnalysisStep'
		return self._oleobj_.InvokeTypes(63, LCID, 1, (24, 0), ((8, 0), (8, 0), (8, 0), (8, 0), (16396, 0)),CellularAnalysisStepXML
			, ImageReferenceXML, PictureExportBuilderName, OutputPicturePathname, p_ObjectCount)

	def TryCellularAnalysisStepEx(self, CellularAnalysisStepXML=defaultNamedNotOptArg, ImageReferenceXML=defaultNamedNotOptArg, PictureExportBuilderName=defaultNamedNotOptArg, OutputPicturePathname=defaultNamedNotOptArg
			, p_ObjectCounts=defaultNamedNotOptArg):
		'method TryCellularAnalysisStepEx'
		return self._oleobj_.InvokeTypes(71, LCID, 1, (24, 0), ((8, 0), (8, 0), (8, 0), (8, 0), (16396, 0)),CellularAnalysisStepXML
			, ImageReferenceXML, PictureExportBuilderName, OutputPicturePathname, p_ObjectCounts)

	def ValidateProcedure(self, p_bRotate180Deg=defaultNamedNotOptArg, pbstrRejectionCause=defaultNamedNotOptArg):
		'method ValidateProcedure'
		return self._oleobj_.InvokeTypes(36, LCID, 1, (3, 0), ((11, 0), (16392, 0)),p_bRotate180Deg
			, pbstrRejectionCause)

	_prop_map_get_ = {
		"Barcode": (2, 2, (8, 0), (), "Barcode", None),
		"CalculationStatus": (47, 2, (3, 0), (), "CalculationStatus", None),
		"Comment": (38, 2, (8, 0), (), "Comment", None),
		"DisKinInterval": (18, 2, (3, 0), (), "DisKinInterval", None),
		"DisKinRuntime": (19, 2, (3, 0), (), "DisKinRuntime", None),
		"DiscontinuousKinetic": (17, 2, (11, 0), (), "DiscontinuousKinetic", None),
		"ID": (1, 2, (8, 0), (), "ID", None),
		"Labware": (53, 2, (11, 0), (), "Labware", None),
		"MaxColumns": (23, 2, (3, 0), (), "MaxColumns", None),
		"MaxRows": (22, 2, (3, 0), (), "MaxRows", None),
		"MaxVessels": (54, 2, (3, 0), (), "MaxVessels", None),
		"Name": (3, 2, (8, 0), (), "Name", None),
		"PlateType": (4, 2, (3, 0), (), "PlateType", None),
		"ReadStatus": (5, 2, (3, 0), (), "ReadStatus", None),
		"SampleCount": (20, 2, (3, 0), (), "SampleCount", None),
		"ValidationUIEnabled": (70, 2, (11, 0), (), "ValidationUIEnabled", None),
	}
	_prop_map_put_ = {
		"Barcode" : ((2, LCID, 4, 0),()),
		"CalculationStatus" : ((47, LCID, 4, 0),()),
		"Comment" : ((38, LCID, 4, 0),()),
		"DisKinInterval" : ((18, LCID, 4, 0),()),
		"DisKinRuntime" : ((19, LCID, 4, 0),()),
		"DiscontinuousKinetic" : ((17, LCID, 4, 0),()),
		"ID" : ((1, LCID, 4, 0),()),
		"Labware" : ((53, LCID, 4, 0),()),
		"MaxColumns" : ((23, LCID, 4, 0),()),
		"MaxRows" : ((22, LCID, 4, 0),()),
		"MaxVessels" : ((54, LCID, 4, 0),()),
		"Name" : ((3, LCID, 4, 0),()),
		"PlateType" : ((4, LCID, 4, 0),()),
		"ReadStatus" : ((5, LCID, 4, 0),()),
		"SampleCount" : ((20, LCID, 4, 0),()),
		"ValidationUIEnabled" : ((70, LCID, 4, 0),()),
	}
	def __iter__(self):
		"Return a Python iterator for this object"
		try:
			ob = self._oleobj_.InvokeTypes(-4,LCID,3,(13, 10),())
		except pythoncom.error:
			raise TypeError("This object does not support enumeration")
		return win32com.client.util.Iterator(ob, None)

class IPlateExportMonitor(DispatchBaseClass):
	CLSID = IID('{28B75D71-F78A-417A-A9E5-2D7F9B16D3F6}')
	coclass_clsid = IID('{B5CC44DB-5EAA-49A9-A6E0-72F23C067141}')

	def GetProgressDetail(self, p_psCompleted=defaultNamedNotOptArg, p_psTotal=defaultNamedNotOptArg):
		'method GetProgressDetail'
		# Result is a Unicode object
		return self._oleobj_.InvokeTypes(3, LCID, 1, (8, 0), ((16396, 0), (16396, 0)),p_psCompleted
			, p_psTotal)

	def RequestAbortion(self):
		'method RequestAbortion'
		return self._oleobj_.InvokeTypes(2, LCID, 1, (24, 0), (),)

	_prop_map_get_ = {
		"ExportInProgress": (1, 2, (11, 0), (), "ExportInProgress", None),
	}
	_prop_map_put_ = {
		"ExportInProgress" : ((1, LCID, 4, 0),()),
	}
	def __iter__(self):
		"Return a Python iterator for this object"
		try:
			ob = self._oleobj_.InvokeTypes(-4,LCID,3,(13, 10),())
		except pythoncom.error:
			raise TypeError("This object does not support enumeration")
		return win32com.client.util.Iterator(ob, None)

class IPlateReadMonitor(DispatchBaseClass):
	CLSID = IID('{8C5C803A-D465-4DF3-B996-663EC0D64A5C}')
	coclass_clsid = IID('{DC9E09F7-1EBD-4BD9-B2A3-7F41FA3CC782}')

	def GetErrorCode(self, ErrorIndex=defaultNamedNotOptArg):
		'method GetErrorCode'
		return self._oleobj_.InvokeTypes(3, LCID, 1, (3, 0), ((3, 0),),ErrorIndex
			)

	def GetErrorMessage(self, ErrorIndex=defaultNamedNotOptArg):
		'method GetErrorMessage'
		# Result is a Unicode object
		return self._oleobj_.InvokeTypes(4, LCID, 1, (8, 0), ((3, 0),),ErrorIndex
			)

	def GetReaderError(self, ErrorIndex=defaultNamedNotOptArg):
		'method GetReaderError'
		return self._oleobj_.InvokeTypes(5, LCID, 1, (3, 0), ((3, 0),),ErrorIndex
			)

	_prop_map_get_ = {
		"BulbWarmupRemainingSeconds": (6, 2, (3, 0), (), "BulbWarmupRemainingSeconds", None),
		"ErrorsCount": (2, 2, (3, 0), (), "ErrorsCount", None),
		"ReadInProgress": (1, 2, (11, 0), (), "ReadInProgress", None),
	}
	_prop_map_put_ = {
		"BulbWarmupRemainingSeconds" : ((6, LCID, 4, 0),()),
		"ErrorsCount" : ((2, LCID, 4, 0),()),
		"ReadInProgress" : ((1, LCID, 4, 0),()),
	}
	def __iter__(self):
		"Return a Python iterator for this object"
		try:
			ob = self._oleobj_.InvokeTypes(-4,LCID,3,(13, 10),())
		except pythoncom.error:
			raise TypeError("This object does not support enumeration")
		return win32com.client.util.Iterator(ob, None)

class IPlates(DispatchBaseClass):
	CLSID = IID('{CA9E1D87-7011-4322-94A7-E95282725B6A}')
	coclass_clsid = IID('{CBBDA8E5-A721-40D9-B677-D12CA91721CC}')

	def Add(self):
		'method Add'
		ret = self._oleobj_.InvokeTypes(4, LCID, 1, (9, 0), (),)
		if ret is not None:
			ret = Dispatch(ret, 'Add', None)
		return ret

	def GetPlate(self, Index=defaultNamedNotOptArg):
		'method GetPlate'
		ret = self._oleobj_.InvokeTypes(3, LCID, 1, (9, 0), ((3, 0),),Index
			)
		if ret is not None:
			ret = Dispatch(ret, 'GetPlate', None)
		return ret

	_prop_map_get_ = {
		"CalibrationCount": (2, 2, (3, 0), (), "CalibrationCount", None),
		"Count": (1, 2, (3, 0), (), "Count", None),
	}
	_prop_map_put_ = {
		"CalibrationCount" : ((2, LCID, 4, 0),()),
		"Count" : ((1, LCID, 4, 0),()),
	}
	def __iter__(self):
		"Return a Python iterator for this object"
		try:
			ob = self._oleobj_.InvokeTypes(-4,LCID,3,(13, 10),())
		except pythoncom.error:
			raise TypeError("This object does not support enumeration")
		return win32com.client.util.Iterator(ob, None)
	#This class has Count() property - allow len(ob) to provide this
	def __len__(self):
		return self._ApplyTypes_(*(1, 2, (3, 0), (), "Count", None))
	#This class has a __len__ - this is needed so 'if object:' always returns TRUE.
	def __nonzero__(self):
		return True

class ISystemTestMonitor(DispatchBaseClass):
	CLSID = IID('{E4308F75-5180-43C8-BB1E-29043281E2AF}')
	coclass_clsid = IID('{3077BF18-B3A4-4C7D-8D97-63AA7DA5333E}')

	def GetSystemTestResults(self):
		'method GetSystemTestResults'
		# Result is a Unicode object
		return self._oleobj_.InvokeTypes(3, LCID, 1, (8, 0), (),)

	_prop_map_get_ = {
		"TestInProgress": (1, 2, (11, 0), (), "TestInProgress", None),
		"TestPassed": (2, 2, (11, 0), (), "TestPassed", None),
	}
	_prop_map_put_ = {
		"TestInProgress" : ((1, LCID, 4, 0),()),
		"TestPassed" : ((2, LCID, 4, 0),()),
	}
	def __iter__(self):
		"Return a Python iterator for this object"
		try:
			ob = self._oleobj_.InvokeTypes(-4,LCID,3,(13, 10),())
		except pythoncom.error:
			raise TypeError("This object does not support enumeration")
		return win32com.client.util.Iterator(ob, None)

from win32com.client import CoClassBaseClass
# This CoClass is known by the name 'Gen5.Application'
class Application(CoClassBaseClass): # A CoClass
	CLSID = IID('{9B3B05F7-143C-4DAF-93D8-726A7BA3321A}')
	coclass_sources = [
	]
	coclass_interfaces = [
		IApplication,
	]
	default_interface = IApplication

class Experiment(CoClassBaseClass): # A CoClass
	CLSID = IID('{F4024CA7-7362-4FC8-B33F-F1F2BD58788F}')
	coclass_sources = [
	]
	coclass_interfaces = [
		IExperiment,
	]
	default_interface = IExperiment

class MonoCalTestMonitor(CoClassBaseClass): # A CoClass
	CLSID = IID('{9EFA02E9-6776-44B3-B193-62A360356658}')
	coclass_sources = [
	]
	coclass_interfaces = [
		IMonoCalTestMonitor,
	]
	default_interface = IMonoCalTestMonitor

class Plate(CoClassBaseClass): # A CoClass
	CLSID = IID('{DA2A9CC3-FE47-441B-BD0C-B482015A525F}')
	coclass_sources = [
	]
	coclass_interfaces = [
		IPlate,
	]
	default_interface = IPlate

class PlateExportMonitor(CoClassBaseClass): # A CoClass
	CLSID = IID('{B5CC44DB-5EAA-49A9-A6E0-72F23C067141}')
	coclass_sources = [
	]
	coclass_interfaces = [
		IPlateExportMonitor,
	]
	default_interface = IPlateExportMonitor

class PlateReadMonitor(CoClassBaseClass): # A CoClass
	CLSID = IID('{DC9E09F7-1EBD-4BD9-B2A3-7F41FA3CC782}')
	coclass_sources = [
	]
	coclass_interfaces = [
		IPlateReadMonitor,
	]
	default_interface = IPlateReadMonitor

class Plates(CoClassBaseClass): # A CoClass
	CLSID = IID('{CBBDA8E5-A721-40D9-B677-D12CA91721CC}')
	coclass_sources = [
	]
	coclass_interfaces = [
		IPlates,
	]
	default_interface = IPlates

class SystemTestMonitor(CoClassBaseClass): # A CoClass
	CLSID = IID('{3077BF18-B3A4-4C7D-8D97-63AA7DA5333E}')
	coclass_sources = [
	]
	coclass_interfaces = [
		ISystemTestMonitor,
	]
	default_interface = ISystemTestMonitor

RecordMap = {
}

CLSIDToClassMap = {
	'{56BBF0D8-DDE6-4F25-BEE1-F3A7CC516531}' : IApplication,
	'{9B3B05F7-143C-4DAF-93D8-726A7BA3321A}' : Application,
	'{21258B83-0AAE-43F7-AFBC-89C680D51C6F}' : IExperiment,
	'{F4024CA7-7362-4FC8-B33F-F1F2BD58788F}' : Experiment,
	'{CA9E1D87-7011-4322-94A7-E95282725B6A}' : IPlates,
	'{CBBDA8E5-A721-40D9-B677-D12CA91721CC}' : Plates,
	'{450BF0EA-F196-4D18-AD0D-DB39D2E6E08B}' : IPlate,
	'{DA2A9CC3-FE47-441B-BD0C-B482015A525F}' : Plate,
	'{8C5C803A-D465-4DF3-B996-663EC0D64A5C}' : IPlateReadMonitor,
	'{DC9E09F7-1EBD-4BD9-B2A3-7F41FA3CC782}' : PlateReadMonitor,
	'{0DABEE12-4422-4FE2-8D4B-F510CA25ECD7}' : IMonoCalTestMonitor,
	'{9EFA02E9-6776-44B3-B193-62A360356658}' : MonoCalTestMonitor,
	'{E4308F75-5180-43C8-BB1E-29043281E2AF}' : ISystemTestMonitor,
	'{3077BF18-B3A4-4C7D-8D97-63AA7DA5333E}' : SystemTestMonitor,
	'{28B75D71-F78A-417A-A9E5-2D7F9B16D3F6}' : IPlateExportMonitor,
	'{B5CC44DB-5EAA-49A9-A6E0-72F23C067141}' : PlateExportMonitor,
}
CLSIDToPackageMap = {}
win32com.client.CLSIDToClass.RegisterCLSIDsFromDict( CLSIDToClassMap )
VTablesToPackageMap = {}
VTablesToClassMap = {
}


NamesToIIDMap = {
	'IApplication' : '{56BBF0D8-DDE6-4F25-BEE1-F3A7CC516531}',
	'IExperiment' : '{21258B83-0AAE-43F7-AFBC-89C680D51C6F}',
	'IPlates' : '{CA9E1D87-7011-4322-94A7-E95282725B6A}',
	'IPlate' : '{450BF0EA-F196-4D18-AD0D-DB39D2E6E08B}',
	'IPlateReadMonitor' : '{8C5C803A-D465-4DF3-B996-663EC0D64A5C}',
	'IMonoCalTestMonitor' : '{0DABEE12-4422-4FE2-8D4B-F510CA25ECD7}',
	'ISystemTestMonitor' : '{E4308F75-5180-43C8-BB1E-29043281E2AF}',
	'IPlateExportMonitor' : '{28B75D71-F78A-417A-A9E5-2D7F9B16D3F6}',
}

win32com.client.constants.__dicts__.append(constants.__dict__)

