# -*- coding: mbcs -*-
# Created by makepy.py version 0.5.01
# By python version 3.9.12 (main, Apr  4 2022, 05:23:19) [MSC v.1916 32 bit (Intel)]
# From type library 'BMG_ActiveX.ocx'
# On Mon Dec  1 11:13:31 2025
"BMG_ActiveX Library"

makepy_version = "0.5.01"
python_version = 0x3090CF0

import pythoncom
import pywintypes
import win32com.client.CLSIDToClass
import win32com.client.util
from pywintypes import IID
from win32com.client import Dispatch

# The following 3 lines may need tweaking for the particular server
# Candidates are pythoncom.Missing, .Empty and .ArgNotFound
defaultNamedOptArg = pythoncom.Empty
defaultNamedNotOptArg = pythoncom.Empty
defaultUnnamedArg = pythoncom.Empty

CLSID = IID("{A7A3B4FA-10E4-4879-A0EF-7618FF0B2042}")
MajorVersion = 1
MinorVersion = 0
LibraryFlags = 8
LCID = 0x0

from win32com.client import DispatchBaseClass


class IBMGRemoteControl(DispatchBaseClass):
    "Dispatch interface for BMGRemoteControl Object"

    CLSID = IID("{9BDB8CCE-8681-435B-BA4A-5F1E5629DFF7}")
    coclass_clsid = IID("{A78E3CF5-8712-4945-BC07-0363BF8BEAC2}")

    def CloseConnection(self):
        return self._oleobj_.InvokeTypes(
            5,
            LCID,
            1,
            (24, 0),
            (),
        )

    def Execute(self, CmdAndParameter=defaultNamedNotOptArg, Result=pythoncom.Missing):
        return self._ApplyTypes_(
            6, 1, (24, 0), ((16396, 1), (16396, 2)), "Execute", None, CmdAndParameter, Result
        )

    def ExecuteAndWait(self, CmdAndParameter=defaultNamedNotOptArg, Result=pythoncom.Missing):
        return self._ApplyTypes_(
            7, 1, (24, 0), ((16396, 1), (16396, 2)), "ExecuteAndWait", None, CmdAndParameter, Result
        )

    def ExecuteAndWait2(self, CmdAndParameter=defaultNamedNotOptArg, Result=pythoncom.Missing):
        return self._ApplyTypes_(
            11,
            1,
            (24, 0),
            ((16396, 1), (16396, 2)),
            "ExecuteAndWait2",
            None,
            CmdAndParameter,
            Result,
        )

    def GetInfo(self, ItemName=defaultNamedNotOptArg, Value=pythoncom.Missing):
        return self._ApplyTypes_(
            2, 1, (24, 0), ((30, 1), (16396, 2)), "GetInfo", None, ItemName, Value
        )

    def GetInfoV(self, ItemName=defaultNamedNotOptArg, Value=pythoncom.Missing):
        return self._ApplyTypes_(
            10, 1, (24, 0), ((16396, 1), (16396, 2)), "GetInfoV", None, ItemName, Value
        )

    def GetVersion(self, Value=pythoncom.Missing):
        return self._ApplyTypes_(8, 1, (24, 0), ((16396, 2),), "GetVersion", None, Value)

    def OpenConnection(self, ServerName=defaultNamedNotOptArg, Result=pythoncom.Missing):
        return self._ApplyTypes_(
            1, 1, (24, 0), ((30, 1), (16396, 2)), "OpenConnection", None, ServerName, Result
        )

    def OpenConnectionV(self, ServerName=defaultNamedNotOptArg, Result=pythoncom.Missing):
        return self._ApplyTypes_(
            9, 1, (24, 0), ((16396, 1), (16396, 2)), "OpenConnectionV", None, ServerName, Result
        )

    def sExecute(
        self,
        CmdName=defaultNamedNotOptArg,
        Parameter1=defaultNamedNotOptArg,
        Parameter2=defaultNamedNotOptArg,
        Parameter3=defaultNamedNotOptArg,
        Parameter4=defaultNamedNotOptArg,
        Parameter5=defaultNamedNotOptArg,
        Parameter6=defaultNamedNotOptArg,
        Parameter7=defaultNamedNotOptArg,
        Parameter8=defaultNamedNotOptArg,
        Parameter9=defaultNamedNotOptArg,
        Result=pythoncom.Missing,
    ):
        return self._ApplyTypes_(
            3,
            1,
            (24, 0),
            (
                (30, 1),
                (30, 1),
                (30, 1),
                (30, 1),
                (30, 1),
                (30, 1),
                (30, 1),
                (30, 1),
                (30, 1),
                (30, 1),
                (16396, 2),
            ),
            "sExecute",
            None,
            CmdName,
            Parameter1,
            Parameter2,
            Parameter3,
            Parameter4,
            Parameter5,
            Parameter6,
            Parameter7,
            Parameter8,
            Parameter9,
            Result,
        )

    def sExecuteAndWait(
        self,
        CmdName=defaultNamedNotOptArg,
        Parameter1=defaultNamedNotOptArg,
        Parameter2=defaultNamedNotOptArg,
        Parameter3=defaultNamedNotOptArg,
        Parameter4=defaultNamedNotOptArg,
        Parameter5=defaultNamedNotOptArg,
        Parameter6=defaultNamedNotOptArg,
        Parameter7=defaultNamedNotOptArg,
        Parameter8=defaultNamedNotOptArg,
        Parameter9=defaultNamedNotOptArg,
        Result=pythoncom.Missing,
    ):
        return self._ApplyTypes_(
            4,
            1,
            (24, 0),
            (
                (30, 1),
                (30, 1),
                (30, 1),
                (30, 1),
                (30, 1),
                (30, 1),
                (30, 1),
                (30, 1),
                (30, 1),
                (30, 1),
                (16396, 2),
            ),
            "sExecuteAndWait",
            None,
            CmdName,
            Parameter1,
            Parameter2,
            Parameter3,
            Parameter4,
            Parameter5,
            Parameter6,
            Parameter7,
            Parameter8,
            Parameter9,
            Result,
        )

    def sExecuteAndWait2(
        self,
        CmdName=defaultNamedNotOptArg,
        Parameter1=defaultNamedNotOptArg,
        Parameter2=defaultNamedNotOptArg,
        Parameter3=defaultNamedNotOptArg,
        Parameter4=defaultNamedNotOptArg,
        Parameter5=defaultNamedNotOptArg,
        Parameter6=defaultNamedNotOptArg,
        Parameter7=defaultNamedNotOptArg,
        Parameter8=defaultNamedNotOptArg,
        Parameter9=defaultNamedNotOptArg,
        Result=pythoncom.Missing,
    ):
        return self._ApplyTypes_(
            12,
            1,
            (24, 0),
            (
                (30, 1),
                (30, 1),
                (30, 1),
                (30, 1),
                (30, 1),
                (30, 1),
                (30, 1),
                (30, 1),
                (30, 1),
                (30, 1),
                (16396, 2),
            ),
            "sExecuteAndWait2",
            None,
            CmdName,
            Parameter1,
            Parameter2,
            Parameter3,
            Parameter4,
            Parameter5,
            Parameter6,
            Parameter7,
            Parameter8,
            Parameter9,
            Result,
        )

    _prop_map_get_ = {}
    _prop_map_put_ = {}

    def __iter__(self):
        "Return a Python iterator for this object"
        try:
            ob = self._oleobj_.InvokeTypes(-4, LCID, 3, (13, 10), ())
        except pythoncom.error:
            raise TypeError("This object does not support enumeration")
        return win32com.client.util.Iterator(ob, None)


from win32com.client import CoClassBaseClass


# This CoClass is known by the name 'BMG_ActiveX.BMGRemoteControl'
class BMGRemoteControl(CoClassBaseClass):  # A CoClass
    # BMGRemoteControl Object
    CLSID = IID("{A78E3CF5-8712-4945-BC07-0363BF8BEAC2}")
    coclass_sources = []
    coclass_interfaces = [
        IBMGRemoteControl,
    ]
    default_interface = IBMGRemoteControl


IBMGRemoteControl_vtables_dispatch_ = 1
IBMGRemoteControl_vtables_ = [
    (
        (
            "OpenConnection",
            "ServerName",
            "Result",
        ),
        1,
        (
            1,
            (),
            [
                (30, 1, None, None),
                (16396, 2, None, None),
            ],
            1,
            1,
            4,
            0,
            28,
            (3, 0, None, None),
            0,
        ),
    ),
    (
        (
            "GetInfo",
            "ItemName",
            "Value",
        ),
        2,
        (
            2,
            (),
            [
                (30, 1, None, None),
                (16396, 2, None, None),
            ],
            1,
            1,
            4,
            0,
            32,
            (3, 0, None, None),
            0,
        ),
    ),
    (
        (
            "sExecute",
            "CmdName",
            "Parameter1",
            "Parameter2",
            "Parameter3",
            "Parameter4",
            "Parameter5",
            "Parameter6",
            "Parameter7",
            "Parameter8",
            "Parameter9",
            "Result",
        ),
        3,
        (
            3,
            (),
            [
                (30, 1, None, None),
                (30, 1, None, None),
                (30, 1, None, None),
                (30, 1, None, None),
                (30, 1, None, None),
                (30, 1, None, None),
                (30, 1, None, None),
                (30, 1, None, None),
                (30, 1, None, None),
                (30, 1, None, None),
                (16396, 2, None, None),
            ],
            1,
            1,
            4,
            0,
            36,
            (3, 0, None, None),
            0,
        ),
    ),
    (
        (
            "sExecuteAndWait",
            "CmdName",
            "Parameter1",
            "Parameter2",
            "Parameter3",
            "Parameter4",
            "Parameter5",
            "Parameter6",
            "Parameter7",
            "Parameter8",
            "Parameter9",
            "Result",
        ),
        4,
        (
            4,
            (),
            [
                (30, 1, None, None),
                (30, 1, None, None),
                (30, 1, None, None),
                (30, 1, None, None),
                (30, 1, None, None),
                (30, 1, None, None),
                (30, 1, None, None),
                (30, 1, None, None),
                (30, 1, None, None),
                (30, 1, None, None),
                (16396, 2, None, None),
            ],
            1,
            1,
            4,
            0,
            40,
            (3, 0, None, None),
            0,
        ),
    ),
    (
        ("CloseConnection",),
        5,
        (
            5,
            (),
            [],
            1,
            1,
            4,
            0,
            44,
            (3, 0, None, None),
            0,
        ),
    ),
    (
        (
            "Execute",
            "CmdAndParameter",
            "Result",
        ),
        6,
        (
            6,
            (),
            [
                (16396, 1, None, None),
                (16396, 2, None, None),
            ],
            1,
            1,
            4,
            0,
            48,
            (3, 0, None, None),
            0,
        ),
    ),
    (
        (
            "ExecuteAndWait",
            "CmdAndParameter",
            "Result",
        ),
        7,
        (
            7,
            (),
            [
                (16396, 1, None, None),
                (16396, 2, None, None),
            ],
            1,
            1,
            4,
            0,
            52,
            (3, 0, None, None),
            0,
        ),
    ),
    (
        (
            "GetVersion",
            "Value",
        ),
        8,
        (
            8,
            (),
            [
                (16396, 2, None, None),
            ],
            1,
            1,
            4,
            0,
            56,
            (3, 0, None, None),
            0,
        ),
    ),
    (
        (
            "OpenConnectionV",
            "ServerName",
            "Result",
        ),
        9,
        (
            9,
            (),
            [
                (16396, 1, None, None),
                (16396, 2, None, None),
            ],
            1,
            1,
            4,
            0,
            60,
            (3, 0, None, None),
            0,
        ),
    ),
    (
        (
            "GetInfoV",
            "ItemName",
            "Value",
        ),
        10,
        (
            10,
            (),
            [
                (16396, 1, None, None),
                (16396, 2, None, None),
            ],
            1,
            1,
            4,
            0,
            64,
            (3, 0, None, None),
            0,
        ),
    ),
    (
        (
            "ExecuteAndWait2",
            "CmdAndParameter",
            "Result",
        ),
        11,
        (
            11,
            (),
            [
                (16396, 1, None, None),
                (16396, 2, None, None),
            ],
            1,
            1,
            4,
            0,
            68,
            (3, 0, None, None),
            0,
        ),
    ),
    (
        (
            "sExecuteAndWait2",
            "CmdName",
            "Parameter1",
            "Parameter2",
            "Parameter3",
            "Parameter4",
            "Parameter5",
            "Parameter6",
            "Parameter7",
            "Parameter8",
            "Parameter9",
            "Result",
        ),
        12,
        (
            12,
            (),
            [
                (30, 1, None, None),
                (30, 1, None, None),
                (30, 1, None, None),
                (30, 1, None, None),
                (30, 1, None, None),
                (30, 1, None, None),
                (30, 1, None, None),
                (30, 1, None, None),
                (30, 1, None, None),
                (30, 1, None, None),
                (16396, 2, None, None),
            ],
            1,
            1,
            4,
            0,
            72,
            (3, 0, None, None),
            0,
        ),
    ),
]

RecordMap = {}

CLSIDToClassMap = {
    "{9BDB8CCE-8681-435B-BA4A-5F1E5629DFF7}": IBMGRemoteControl,
    "{A78E3CF5-8712-4945-BC07-0363BF8BEAC2}": BMGRemoteControl,
}
CLSIDToPackageMap = {}
win32com.client.CLSIDToClass.RegisterCLSIDsFromDict(CLSIDToClassMap)
VTablesToPackageMap = {}
VTablesToClassMap = {
    "{9BDB8CCE-8681-435B-BA4A-5F1E5629DFF7}": "IBMGRemoteControl",
}


NamesToIIDMap = {
    "IBMGRemoteControl": "{9BDB8CCE-8681-435B-BA4A-5F1E5629DFF7}",
}
