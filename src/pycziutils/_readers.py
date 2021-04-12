# coding: utf-8
# This file contains modified source code from python-bioformats ( https://github.com/CellProfiler/python-bioformats ), 
# which is licensed under BSD license. For details, see LICENSE.

import bioformats
import javabridge
from javabridge import jutil
import functools


def get_tiled_reader(path):
    """
    Read tiled czi image and get ZeissCZIReader without stitching

    Parameters
    ---------
    path : str
        path to the czi file

    Returns
    -------
    reader : ZeissCZIReader
        tiled reader
    """
    CZIAllowStitchKey = jutil.get_static_field(
        "loci/formats/in/ZeissCZIReader",
        "ALLOW_AUTOSTITCHING_KEY",
        "Ljava/lang/String;",
    )
    CZIIncludeAttachmentKey = jutil.get_static_field(
        "loci/formats/in/ZeissCZIReader",
        "INCLUDE_ATTACHMENTS_KEY",
        "Ljava/lang/String;",
    )
    jutil.set_static_field(
        "loci/formats/in/ZeissCZIReader", "ALLOW_AUTOSTITCHING_DEFAULT", "Z", False
    )
    jutil.set_static_field(
        "loci/formats/in/ZeissCZIReader", "INCLUDE_ATTACHMENTS_DEFAULT", "Z", False
    )
    rdr = bioformats.ImageReader(path, perform_init=False)
    DynamicMetadataOptions = javabridge.JClassWrapper(
        "loci.formats.in.DynamicMetadataOptions"
    )
    dynop = DynamicMetadataOptions()
    dynop.set(CZIAllowStitchKey, "false")
    dynop.set(CZIIncludeAttachmentKey, "false")
    rdr.rdr.setMetadataOptions(dynop)
    rdr.metadata = bioformats.metadatatools.createOMEXMLMetadata()
    rdr.rdr.setMetadataStore(rdr.metadata)
    rdr.rdr.setId(rdr.path)
    return rdr


def get_tiled_omexml_metadata(path=None, url=None, *, group_file=True):
    """
    Read tiled czi image and get ZeissCZIReader without stitching

    Parameters
    ---------
    path : str, default None
        path to the czi file
    url : str, default None
        url to the czi file (optional)
    groupfiles: bool, default True
        utilize the groupfiles option to take the directory structure into account.

    Returns
    -------
    xml : str
        the OME-XML string

    Notes
    -----
    Copied & modified from bioformats.get_omexml_metadata
    """

    with bioformats.ImageReader(path=path, url=url, perform_init=False) as rdr:
        #
        # Below, "in" is a keyword and Rhino's parser is just a little wonky I fear.
        #
        # It is critical that setGroupFiles be set to false, goodness knows
        # why, but if you don't the series count is wrong for flex files.
        #
        script = f"""
        importClass(Packages.loci.common.services.ServiceFactory,
                    Packages.loci.formats.services.OMEXMLService,
                    Packages.loci.formats['in'].ZeissCZIReader,
                    Packages.loci.formats['in'].DefaultMetadataOptions,
                    Packages.loci.formats['in'].DynamicMetadataOptions,
                    Packages.loci.formats['in'].MetadataLevel);
        reader.setGroupFiles({'true' if group_file else 'false'});
        reader.setOriginalMetadataPopulated(true);
        var service = new ServiceFactory().getInstance(OMEXMLService);
        var metadata = service.createOMEXMLMetadata();
        reader.setMetadataStore(metadata);
        reader.setMetadataOptions(new DefaultMetadataOptions(MetadataLevel.ALL));
        var dynop=DynamicMetadataOptions();
        dynop.set(ZeissCZIReader.ALLOW_AUTOSTITCHING_KEY,'false');
        dynop.set(ZeissCZIReader.INCLUDE_ATTACHMENTS_KEY,'false');
        reader.setMetadataOptions(dynop);
        reader.setId(path);
        var xml = service.getOMEXML(metadata);
        xml;
        """
        xml = jutil.run_script(script, dict(path=rdr.path, reader=rdr.rdr))
    return xml


def with_javabridge(func):
    """
    runs function with javabridge, with the loglevel error
    https://forum.image.sc/t/python-bioformats-and-javabridge-debug-messages/12578/11
    """
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        try:
            javabridge.start_vm(class_path=bioformats.JARS)
            myloglevel = "ERROR"  # user string argument for logLevel.
            rootLoggerName = javabridge.get_static_field(
                "org/slf4j/Logger", "ROOT_LOGGER_NAME", "Ljava/lang/String;"
            )
            rootLogger = javabridge.static_call(
                "org/slf4j/LoggerFactory",
                "getLogger",
                "(Ljava/lang/String;)Lorg/slf4j/Logger;",
                rootLoggerName,
            )
            logLevel = javabridge.get_static_field(
                "ch/qos/logback/classic/Level",
                myloglevel,
                "Lch/qos/logback/classic/Level;",
            )
            javabridge.call(
                rootLogger, "setLevel", "(Lch/qos/logback/classic/Level;)V", logLevel
            )
            return func(*args, **kwargs)
        finally:
            javabridge.kill_vm()

    return wrapped
