#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `pycziutils` package."""

import os
from glob import glob
from os import path

import numpy as np
import pycziutils
import pytest


def parse_filename(filename):
    properties = [
        p.split("-") for p in path.basename(filename).replace(".czi", "").split("_")
    ]
    properties = {p[0]: p[1:] for p in properties}
    properties["tile"] = list(map(int, properties["tile"][0].split("x")))
    properties["binning"] = list(map(int, properties["binning"][0].split("x")))
    for k in properties.keys():
        try:
            properties[k] = list(map(int, properties[k]))
        except ValueError:
            pass
    for k in ["time", "z", "bitdepth"]:
        assert len(properties[k]) == 1
        properties[k] = properties[k][0]
    return properties


@pytest.fixture
def czi_files_path(shared_datadir):
    files = glob(path.join(shared_datadir, "*.czi"))
    filedata = [parse_filename(f) for f in files]
    return list(zip(files, filedata))


def test_if_test_files_exists(czi_files_path, shared_datadir):
    assert len(czi_files_path) > 0
    assert len(czi_files_path) == len(os.listdir(shared_datadir))
    for name, data in czi_files_path:
        print(name)
        print(data)
        assert path.isfile(name)


def assert_indices(series, index_max):
    assert np.array_equal(np.sort(series.unique()), np.arange(index_max))


@pycziutils.with_javabridge
def test_read_images_by_dataframe(czi_files_path):
    for name, data in czi_files_path:
        tiled_czi_ome_xml = pycziutils.get_tiled_omexml_metadata(name)
        tiled_properties_dataframe = pycziutils.parse_planes(tiled_czi_ome_xml)
        print(tiled_properties_dataframe.columns)
        # Index(['index', 'X', 'Y', 'Z', 'T', 'C_index', 'T_index', 'Z_index', 'image',
        #       'plane', 'image_acquisition_T', 'absolute_T'],
        #        dtype='object')
        print(tiled_properties_dataframe.iloc[0])
        # index                                                 0
        # X                                             -1165.624
        # Y                                               122.694
        # Z                                                 0.001
        # T                                                 1.027
        # C_index                                               0
        # T_index                                               0
        # Z_index                                               0
        # image                                                 0
        # plane                                                 0
        # image_acquisition_T    2021-04-12 02:12:21.340000+00:00
        # absolute_T             2021-04-12 02:12:22.367000+00:00
        # Name: 0, dtype: object

        assert_indices(
            tiled_properties_dataframe["image"], data["tile"][0] * data["tile"][1]
        )
        assert_indices(tiled_properties_dataframe["C_index"], len(data["channel"]))
        assert_indices(tiled_properties_dataframe["T_index"], data["time"])
        assert_indices(tiled_properties_dataframe["Z_index"], data["z"])

        # returns bioformats reader for tiled images
        reader = pycziutils.get_tiled_reader(name)  
        for _, row in tiled_properties_dataframe.iterrows():
            image = reader.read(
                series=row["image"],
                t=row["T_index"],
                z=row["Z_index"],
                c=row["C_index"],
            )
