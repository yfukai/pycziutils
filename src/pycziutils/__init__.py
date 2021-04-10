# coding: utf-8
"""
pycziutils

A tiny utility module to parse Zeiss CZI files in Python through python-bioformats.
Parse tiled images, organize planes into pandas.DataFrame, get some hard-to-get metadata.

Example
-------
tiled_czi_reader=pycziutils.get_tiled_czi_reader("path/to/czi/file.czi")
tiled_czi_ome_xml=pycziutils.get_tiled_omexml_metadata("path/to/czi/file.czi")
tile_properties_dataframe=pycziutils.get_planes(tiled_czi_ome_xml)
bit_depth=pycziutils.get_camera_bits(tiled_czi_ome_xml)

# bonous:
@with_javabridge
def function_using_javabridge():
    pass # do whatever you like to do with javabridge, with adjusted log level!

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

__all__ = [name for name in dir() if not name.startswith("_")]
