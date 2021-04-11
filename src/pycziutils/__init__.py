# coding: utf-8
"""
pycziutils

A tiny utility module to parse Zeiss CZI files in Python through python-bioformats.
Parse tiled images, organize planes into pandas.DataFrame, get some hard-to-get metadata.

"""

__author__ = """Yohsuke T. Fukai"""
__email__ = "ysk@yfukai.net"
__version__ = "0.1.0"

from ._parsers import (
    parse_binning,
    parse_camera_bits,
    parse_camera_LUT,
    parse_camera_roi,
    parse_camera_roi_slice,
    parse_channels,
    parse_pixel_size,
    parse_planes,
    parse_properties,
    parse_structured_annotation_dict,
)
from ._readers import get_tiled_omexml_metadata, get_tiled_reader

# __all__ = [name for name in dir() if not name.startswith("_")]
__all__ = [
    "parse_binning",
    "parse_camera_bits",
    "parse_camera_LUT",
    "parse_camera_roi",
    "parse_camera_roi_slice",
    "parse_channels",
    "parse_pixel_size",
    "parse_planes",
    "parse_properties",
    "parse_structured_annotation_dict",
    "get_tiled_omexml_metadata",
    "get_tiled_reader",
]
