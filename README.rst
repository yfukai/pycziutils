==========
pycziutils
==========


.. image:: https://img.shields.io/pypi/v/pycziutils.svg
        :target: https://pypi.python.org/pypi/pycziutils

.. image:: https://readthedocs.org/projects/pycziutils/badge/?version=latest
        :target: https://pycziutils.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


Python utilities to read (tiled) CZI files and parse metadata through python-bioformats


* Free software: BSD license

* Documentation: https://pycziutils.readthedocs.io.


Installation
------------

.. code-block:: console

    $ pip install pycziutils

Features
--------

A tiny utility module to parse Zeiss CZI files in Python through python-bioformats.
Parse tiled images, organize planes into pandas.DataFrame, parse some hard-to-get metadata.

Example
-------

.. code-block:: python
    
    import pycziutils


    @pycziutils.with_javabridge
    def main():
        czi_file_path="path/to/czi/file.czi"
        tiled_czi_ome_xml=pycziutils.get_tiled_omexml_metadata(czi_file_path)
        tiled_properties_dataframe=pycziutils.parse_planes(tiled_czi_ome_xml)

        print(tiled_properties_dataframe.columns)
        #Index(['index', 'X', 'Y', 'Z', 'T', 'C_index', 'T_index', 'Z_index', 'image',
        #       'plane', 'image_acquisition_T', 'absolute_T'],
        #        dtype='object')

        print(tiled_properties_dataframe.iloc[0])
        #index                                                 0
        #X                                             -1165.624
        #Y                                               122.694
        #Z                                                 0.001
        #T                                                 1.027
        #C_index                                               0
        #T_index                                               0
        #Z_index                                               0
        #image                                                 0
        #plane                                                 0
        #image_acquisition_T    2021-04-12 02:12:21.340000+00:00
        #absolute_T             2021-04-12 02:12:22.367000+00:00
        #Name: 0, dtype: object

        #returns bioformats reader for tiled images
        reader=pycziutils.get_tiled_reader(czi_file_path) 
        for i, row in tiled_properties_dataframe.iterrows():
            image = reader.read(
                series=row["image"],
                t=row["T_index"],
                z=row["Z_index"],
                c=row["C_index"],
            )
   
    if __name__=="__main__":
        main()

TODO
----
- Get the doc hosted in readthedocs (fix installation problem)
- Github actions
- Writing tests for _parsers.py

Credits
-------

This package was created with Cookiecutter_ and the `wboxx1/cookiecutter-pypackage-poetry`_ project template.

This package is using pysen_ for linting and formatting. 

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`wboxx1/cookiecutter-pypackage-poetry`: https://github.com/wboxx1/cookiecutter-pypackage-poetry
.. _pysen: https://github.com/pfnet/pysen
