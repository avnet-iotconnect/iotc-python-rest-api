# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

from dataclasses import Field, fields
from typing import TypeVar, Protocol, ClassVar, Any, Type


# Credit: "intgr" at stackoverflow example https://stackoverflow.com/questions/61736151/how-to-make-a-typevar-generic-type-in-python-with-dataclass-constraint
class DataclassInstance(Protocol):
    __dataclass_fields__: ClassVar[dict[str, Field[Any]]]

T = TypeVar('T', bound=DataclassInstance)


def filter_dict_to_dataclass_fields(item: dict, dc: Type[T]) -> dict:
    """Filter a dictionary to include only fields defined in the dataclass."""
    valid_fields = {f.name for f in fields(dc)}
    return {k: v for k, v in item.items() if k in valid_fields}

def normalize_keys(item: dict) -> dict:
    """Replace dashes with underscores in dictionary keys to match dataclass field names."""
    return {key.replace('-', '_'): value for key, value in item.items()}