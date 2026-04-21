from nomad.config.models.plugins import SchemaPackageEntryPoint
from nomad.metainfo import SchemaPackage

m_package = SchemaPackage()


class MagnetometrySchemaPackageEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from . import agm_schema, vsm_schema

        _ = (agm_schema, vsm_schema)

        return m_package


schema_package_entry_point = MagnetometrySchemaPackageEntryPoint(
    name='Magnetometry Schemas',
    description='Schemas for Magnetometry (VSM, AGM, etc) data.',
)
