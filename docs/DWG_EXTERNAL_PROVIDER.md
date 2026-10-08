# DWG Production Provider

StructuralPro uses a provider-neutral DWG boundary:

**DWG → authorized external converter → DXF → ezdxf → extraction/takeoff**

The desktop application does **not** bundle an unlicensed native DWG parser.

## Configuring a provider

Configure an installed, authorized command-line DWG converter through the `ExternalDWGConverterProvider`:

- executable path/name
- target output version (default `ACAD2018`)
- audit flag (default enabled)
- recursive flag (default disabled)
- conversion timeout

The adapter invokes the converter explicitly, requires exactly one generated DXF artifact, validates that artifact with the existing real `ezdxf` parser, and only then exposes the document to the CAD/takeoff pipeline.

Missing executable, conversion failure, timeout, zero/multiple output files, or invalid generated DXF all fail closed.

## ODA File Converter

ODA publishes a free ODA File Converter application for DWG/DXF conversion and documents a command-line interface. ODA states that non-members may use its free example applications for **non-commercial applications only**. Therefore StructuralPro must not silently bundle or redistribute ODA File Converter as a commercial product without the required ODA rights.

For commercial distribution, use an appropriately licensed provider and record its license, version, checksum and redistribution rights in the release evidence inventory.

## Security / integrity

The converter is treated as an external evidence provider. StructuralPro does not infer engineering quantities from the DWG bytes. Geometry is consumed only after conversion and validation by the existing DXF parser.

See:
- `core/cad/external_dwg_provider_v1.py`
- `core/cad/provider_registry_v1.py`
- `core/cad/ezdxf_provider_v1.py`
