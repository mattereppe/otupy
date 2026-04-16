5.22 Xbom
=========

Abstract base class for eXtended Bill of Materials (XBOM). This abstract class defines the minimal interface that all XBOM implementations must follow. Actuators work with this interface, allowing different BOM formats to be used interchangeably without changes to the actuator code.

Type: :py:class:`~otupy.profiles.xbom.data.abstract_xbom.Xbom` (:py:class:`~otupy.types.base.record.Record`)


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
     - Format of the XBOM
   * - 2
     - bom
     - ``Any``
     - 0..1
     - Bill of Materials object (format-specific)

**Abstract Methods:**

* **add(item)**: Adds an item to the XBOM. This method must implement the logic to handle the different types of items that can be added to the XBOM.
* **add_dependency_with_external_ref(depends_on_xbom, comment)**: Add both an external reference and a dependency to another XBOM.

**Polymorphic Deserialization:**

When deserializing to the abstract Xbom type, the ``fromdict`` method inspects the 'format' field to determine the correct concrete subclass to use. If the format is not specified or not found, it defaults to CyclonedxXbom.

