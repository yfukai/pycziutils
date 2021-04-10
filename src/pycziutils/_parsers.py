import copy
import json
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import xmltodict


def __wrap_list(x):
    if isinstance(x, list):
        return x
    else:
        return [x]


def __copy_keys(x, keys):
    #    print(x,keys)
    if not isinstance(keys, list):
        return copy.deepcopy(x[keys])
    else:
        return [copy.deepcopy(x.get(key, None)) for key in keys]


def parse_properties(ome_xml, keys, domain="pixels"):
    """
    parse OME-XML and get properties of the specified domain

    Parameters
    ----------
    ome_xml : str
        the input OME-XML string
    keys :
        the keys for the properties
    domain : str
        the domain level to get properties, should be "image", "pixels" or "plane"

    Returns
    -------
    properties :
        the properties as a list
    """
    meta_dict = xmltodict.parse(ome_xml)
    images = __wrap_list(meta_dict["OME"]["Image"])

    if domain == "image":
        return [__copy_keys(im, keys) for im in images]
    elif domain == "pixels":
        return [__copy_keys(im["Pixels"], keys) for im in images]
    elif domain == "plane":
        return [
            [__copy_keys(pl, keys) for pl in __wrap_list(im["Pixels"]["Plane"])]
            for im in images
        ]
    else:
        raise ValueError("domain must be plane, pixels or image")


def parse_channels(ome_xml, assume_all_equal=True):
    """
    parse OME-XML and get the channel list

    Parameters
    ----------
    ome_xml : str
        the input OME-XML string
    assume_all_equal : bool, default True
        if True, assume the channels are the same for all the planes

    Returns
    -------
    channels :
        a list of channels if assume_all_equal==True,
        otherwise a list of lists of channels for each planes
    """
    channelss = parse_properties(ome_xml, "Channel")
    _channelss = []
    for cc in channelss:
        _cc = __wrap_list(cc)
        for c in _cc:
            del c["@ID"]
        _channelss.append(_cc)
    channelss = _channelss

    if assume_all_equal:
        assert all([c == channelss[0] for c in channelss])
        return channelss[0]
    else:
        return channelss


def parse_pixel_size(ome_xml, assume_all_equal=True):
    """
    parse OME-XML and get the pixel sizes

    Parameters
    ----------
    ome_xml : str
        the input OME-XML string
    assume_all_equal : bool, default True
        if True, assume the pixel sizes are the same for all the planes

    Returns
    -------
    pixel sizes :
        a list of pixel sizes if assume_all_equal==True,
        otherwise a list of lists of pixel sizes for each planes
    """
    keys = [
        "@PhysicalSizeX",
        "@PhysicalSizeXUnit",
        "@PhysicalSizeY",
        "@PhysicalSizeYUnit",
    ]
    props = parse_properties(ome_xml, keys)
    if assume_all_equal:
        assert np.all(
            [np.all([props[0][i] == p[i] for i in range(len(keys))]) for p in props]
        )
        return props[0]
    else:
        return props


def parse_planes(ome_xml, acquisition_timezone=0):
    """
    parse OME-XML and get pandas dataframe for each planes

    Parameters
    ----------
    ome_xml : str
        the input OME-XML string
    acquisition_timezone : Union[datetime.timezone, int]
        timezone to use. if int is given,
        datetime.timezone(datetime.timedelta(timezone)) is used

    Returns
    -------
    planes_df : pandas.DataFrame
        dataframe for all planes, containing X,Y,Z positions and time

    Note
    ----
    absolute_T is T + AcquisitionDate, not sure if it is absolutely correct for now

    """
    keys = [
        "@PositionX",
        "@PositionY",
        "@PositionZ",
        "@DeltaT",
        "@TheC",
        "@TheT",
        "@TheZ",
    ]
    names = ["X", "Y", "Z", "T", "C_index", "T_index", "Z_index"]
    positions = parse_properties(ome_xml, keys, domain="plane")
    acq_dates = parse_properties(ome_xml, "AcquisitionDate", domain="image")
    assert len(positions) == len(acq_dates)
    planes_df = pd.DataFrame()
    for j, (ps, acq_date) in enumerate(zip(positions, acq_dates)):
        df = pd.DataFrame(data=ps, columns=names, dtype=np.float64)
        df["image"] = j
        df["plane"] = range(len(ps))

        if isinstance(acquisition_timezone, int):
            acquisition_timezone = timezone(timedelta(hours=acquisition_timezone))
        acq_date = (
            datetime.strptime(acq_date, "%Y-%m-%dT%H:%M:%S.%f")
            .replace(tzinfo=timezone.utc)
            .astimezone(acquisition_timezone)
        )
        df["image_acquisition_T"] = acq_date

        planes_df = planes_df.append(df)
    for k in [n for n in names if "index" in n] + ["image", "plane"]:
        planes_df[k] = planes_df[k].astype(int)
    planes_df["absolute_T"] = planes_df["image_acquisition_T"] + np.vectorize(
        timedelta
    )(seconds=planes_df["T"])
    planes_df = planes_df.reset_index()
    return planes_df


def summarize_image_size(reader, print_summary=True):
    """
    get image size and summarize from reader

    Parameters
    ----------
    reader :
        the bioformat reader
    print_summary : bool, default True
        wheather to print the size summary

    Returns
    -------
        seriesCount : int
            the count for series
        sizeT : int
            the count for time
        sizeC : int
            the count for channels
        sizeX : int
            the count for X
        sizeY : int
            the count for Y
        sizeZ : int
            the count for Z

    """
    seriesCount = reader.rdr.getSeriesCount()
    sizeT = reader.rdr.getSizeT()
    sizeC = reader.rdr.getSizeC()
    sizeX = reader.rdr.getSizeX()
    sizeY = reader.rdr.getSizeY()
    sizeZ = reader.rdr.getSizeZ()
    if print_summary:
        print("series count:", seriesCount)
        print("sizeT:", sizeT)
        print("sizeC:", sizeC)
        print("sizeX:", sizeX)
        print("sizeY:", sizeY)
        print("sizeZ:", sizeZ)
    return seriesCount, sizeT, sizeC, sizeX, sizeY, sizeZ


def parse_structured_annotation_dict(ome_xml):
    """
    parse OME-XML and get structured annotation as a dict

    Parameters
    ----------
    ome_xml : str
        the input OME-XML string

    Returns
    -------
    structured_annotation_dict : dict
        OriginalMetadata.key : OriginalMetadata.value pairs as a dict

    """
    meta_dict = xmltodict.parse(ome_xml)
    annotation = meta_dict["OME"]["StructuredAnnotations"]["XMLAnnotation"]
    return {
        a["Value"]["OriginalMetadata"]["Key"]: a["Value"]["OriginalMetadata"]["Value"]
        for a in annotation
    }


def parse_binning(ome_xml):
    """
    parse OME-XML and get binning

    Parameters
    ----------
    ome_xml : str
        the input OME-XML string

    Returns
    -------
    binning : list
        the binning as [x,y]

    Note
    ----
    uses 'HardwareSetting|ParameterCollection|Binning'

    """
    annotation_dict = parse_structured_annotation_dict(ome_xml)
    binning = json.loads(annotation_dict["HardwareSetting|ParameterCollection|Binning"])
    return list(binning)


def parse_camera_roi(ome_xml):
    """
    parse OME-XML and get ROI

    Parameters
    ----------
    ome_xml : str
        the input OME-XML string

    Returns
    -------
    roi : list
        the camera ROI (x0,y0,x1,y1) as a list

    Note
    ----
    uses 'HardwareSetting|ParameterCollection|ImageFrame'

    """
    annotation_dict = parse_structured_annotation_dict(ome_xml)
    roi = json.loads(
        annotation_dict["HardwareSetting|ParameterCollection|ImageFrame"]
    )  # or 'HardwareSetting|ParameterCollection|Frame'?
    return list(roi)[:4]


def parse_camera_roi_slice(ome_xml):
    """
    parse OME-XML and get ROI as slices

    Parameters
    ----------
    ome_xml : str
        the input OME-XML string

    Returns
    -------
    roi : slice
        the camera ROI as slices; slice(x0,x0),slice(y0,y1)

    Note
    ----
    uses 'HardwareSetting|ParameterCollection|ImageFrame'

    """
    roi = list(map(int, parse_camera_roi(ome_xml)))
    return slice(roi[0], roi[2] + roi[0]), slice(roi[1], roi[3] + roi[1])


def parse_camera_LUT(ome_xml):
    """
    parse OME-XML and get camera LUT

    Parameters
    ----------
    ome_xml : str
        the input OME-XML string

    Returns
    -------
    lut : list
        the LUT as [lut1,lut2]. If the key is not found, returns (np.nan,np.nan)

    Note
    ----
    uses 'HardwareSetting|ParameterCollection|CameraLUT1' and
         'HardwareSetting|ParameterCollection|CameraLUT2'

    """
    annotation_dict = parse_structured_annotation_dict(ome_xml)
    try:
        lut1 = json.loads(
            annotation_dict["HardwareSetting|ParameterCollection|CameraLUT1"]
        )
        lut2 = json.loads(
            annotation_dict["HardwareSetting|ParameterCollection|CameraLUT2"]
        )
        assert len(lut1) == 1
        assert len(lut2) == 1
        return (lut1[0], lut2[0])
    except KeyError:
        return (np.nan, np.nan)


def parse_camera_bits(ome_xml):
    """
    parse OME-XML and get camera bits

    Parameters
    ----------
    ome_xml : str
        the input OME-XML string

    Returns
    -------
    bit_depth : int
        the camera valid bits

    Note
    ----
    uses 'HardwareSetting|ParameterCollection|ValidBits'

    """
    annotation_dict = parse_structured_annotation_dict(ome_xml)
    res = list(
        json.loads(annotation_dict["HardwareSetting|ParameterCollection|ValidBits"])
    )
    assert len(res) == 1
    return res[0]
