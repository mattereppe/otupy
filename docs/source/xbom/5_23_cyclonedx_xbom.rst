5.23 CyclonedxXbom
==================

CycloneDX implementation of XBOM. This is the concrete implementation that uses the CycloneDX library to provide eXtended Bill of Materials functionality.

Type: :py:class:`~otupy.profiles.xbom.data.xbom.CyclonedxXbom` (:py:class:`~otupy.profiles.xbom.data.abstract_xbom.Xbom`)


.. list-table::
   :widths: 3 5 5 5 45
   :header-rows: 1

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1
     - format
     - :py:class:`~otupy.profiles.xbom.data.sbom_format.SbomFormat`
     - 1
     - Format of the XBOM (always set to ``cyclonedx``)
   * - 2
     - bom
     - ``cyclonedx.model.bom.Bom``
     - 0..1
     - CycloneDX Bill of Materials object

**Key Methods:**

* **add(item)**: Add an item to the BOM. Accepts Components, Services, Dependencies, Properties, or objects with an ``as_cyclonedx()`` method.
* **get_bom_serial_number()**: Get or create the BOM's serial number (UUID). If not set, a new UUID will be generated and assigned.
* **get_bom_version()**: Get the BOM's version number (defaults to 1 if not set).
* **get_bom_link(element_bom_ref)**: Generate a CycloneDX bom-link URI for an element in this BOM. Format: ``urn:cdx:{serial-number}/{version}#{bom-ref}``
* **get_bom_ref()**: Get the bom_ref of the main component or service in this XBOM.
* **get_main_item()**: Get the main component or service in this XBOM (ignores stub components/services with external references).
* **add_external_reference(url, ref_type, comment)**: Add an external reference to the main component or service. Used to link to other BOMs.
* **add_dependency(depends_on_ref)**: Add a dependency from the main item in this XBOM to another component/service identified by its bom_ref.
* **add_dependency_with_external_ref(depends_on_xbom, comment)**: Add both an external reference and a dependency to another XBOM.

**Notes:**

* The BOM uses CycloneDX Schema Version 1.7
* External references are used to link to other BOMs that contain related components
* Dependencies create CycloneDX dependency relationships between components/services
