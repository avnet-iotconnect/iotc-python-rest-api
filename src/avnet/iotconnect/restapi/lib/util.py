# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.
import hashlib
# The JSON to object mapping was originally created with assistance from OpenAI's ChatGPT.
# For more information about ChatGPT, visit https://openai.com/

from dataclasses import Field, fields
from dataclasses import is_dataclass
from datetime import datetime, timezone
from typing import TypeVar, Protocol, ClassVar, Any, Type
from typing import Union, get_type_hints


# Credit: "intgr" at stackoverflow example https://stackoverflow.com/questions/61736151/how-to-make-a-typevar-generic-type-in-python-with-dataclass-constraint
class DataclassInstance(Protocol):
    __dataclass_fields__: ClassVar[dict[str, Field[Any]]]

T = TypeVar('T', bound=DataclassInstance)


# unique alphanumeric-sortable timestamp string - generated based on current time like 250317.185311.483
def generate_unique_timestamp_string():
    return datetime.now(timezone.utc).strftime("%y%m%d.%H%M%S.%f")[:-3]  # Milliseconds precision with 3 most significant digits


def filter_dict_to_dataclass_fields(item: dict, dc: Type[T]) -> dict:
    """Filter a dictionary to include only fields defined in the dataclass."""
    valid_fields = {f.name for f in fields(dc)}
    return {k: v for k, v in item.items() if k in valid_fields}

def normalize_keys(item: dict) -> dict:
    """Replace dashes with underscores in dictionary keys to match dataclass field names."""
    return {key.replace('-', '_'): value for key, value in item.items()}

# credit: https://stackoverflow.com/questions/16874598/how-to-calculate-the-md5-checksum-of-a-file-in-python
def file_md5(filename: str):
    with open(filename, 'rb') as f:
        file_hash = hashlib.md5()
        while chunk := f.read(1024 * 20): # 20k at a time
            file_hash.update(chunk)
        return file_hash.hexdigest()

def _is_optional_or_dataclass(field_type, value):
    """
    Check if a field type is either an Optional or a dataclass.
    """
    if hasattr(field_type, '__origin__') and field_type.__origin__ is Union:
        # Check for Optional[Type]
        inner_types = field_type.__args__
        if len(inner_types) == 2 and type(None) in inner_types:
            inner_type = [t for t in inner_types if t is not type(None)][0]
            return is_dataclass(inner_type)
    return is_dataclass(field_type)

def deserialize_dataclass(cls: Type[T], data: Union[dict, list]) -> T:
    """
    Recursively deserialize data into a dataclass or a list of dataclasses.
    """
    if isinstance(data, list):
        # Handle lists of dataclasses
        inner_type = cls.__args__[0] if hasattr(cls, '__args__') else None
        if inner_type and is_dataclass(inner_type):
            return [deserialize_dataclass(inner_type, item) for item in data]
        return data

    if isinstance(data, dict) and is_dataclass(cls):
        field_types = get_type_hints(cls)
        return cls(
            **{
                key: deserialize_dataclass(field_types[key], value)
                if key in field_types and _is_optional_or_dataclass(field_types[key], value)
                else (
                    deserialize_dataclass(field_types[key], value)
                    if key in field_types
                       and hasattr(field_types[key], '__origin__')
                       and field_types[key].__origin__ == list
                    else value
                )
                for key, value in data.items()
                if key in field_types  # Ignore unexpected fields
            }
        )
    return data