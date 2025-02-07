from google.protobuf.struct_pb2 import Struct
import typing as t

def struct_to_dict(struct: Struct) -> t.Any:
    out = {}
    for key, value in struct.items():
        if isinstance(value, Struct):
            out[key] = struct_to_dict(value)
        else:
            out[key] = value
    return out
