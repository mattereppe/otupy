2. Data model
=============

The main purpose for the XBOM profile is to return a Bill of Materials (BOM)
of the execution environment, focusing on Extended Bill of Materials (XBOM)
compliant with the CycloneDX standard.

The data model of the returned data revolves around the following key concept:

-  :py:class:`~otupy.profiles.xbom.data.xbom.Xbom`:
    This is the main object that encapsulates the XBOM. It contains the
    BOM data, typically in CycloneDX format, representing the components,
    services, and dependencies.
    It includes:

    * :py:class:`~otupy.profiles.xbom.data.sbom_format.SbomFormat`
	  The format of the XBOM (e.g., CycloneDX).
	  -- cite the bom attribute of the xbom class below --
    * :py:attribute:`~otupy.profiles.xbom.data.bom.Bom`
        the `cyclonedx-python-lib` library's :py:class:`cyclonedx.model.bom.Bom` class.
    .. *   **bom**: The actual Bill of Materials object, which is based on
    ..     the `cyclonedx-python-lib` library's :py:class:`cyclonedx.model.bom.Bom` class.

The XBOM profile heavily relies on the data structures provided by the
libraries that implement the various BOM formats. For CycloneDX, the
`cyclonedx-python-lib` library is used, which provides comprehensive classes
to represent BOMs, components, and related metadata.

