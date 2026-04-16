from pathlib import Path
from typing import TYPE_CHECKING

from nomad.datamodel.context import ServerContext
from nomad.parsing import MatchingParser

from nomad_measurements_magnetometry.schema_packages.schema_package import (
    ELNVibratingSampleMagnetometry,
)

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger


class VSMParser(MatchingParser):
    def is_mainfile(self, filename: str, mime: str, buffer: bytes, decoded_buffer: str, compression: str = None) -> bool:
        """
        Gatekeeper: Only returns True if the file contains Lake Shore VSM headers.
        """
        # 1. Standard regex check (handles the .csv extension)
        is_csv = super().is_mainfile(filename, mime, buffer, decoded_buffer, compression)
        if not is_csv:
            return False

        # 2. Check for the actual headers found in your data files
        if decoded_buffer:
            # Check for the very first line or the configuration blocks
            if '#RUN ON SOFTWARE VERSION' in decoded_buffer or '#FIELD CONFIGURATIONS' in decoded_buffer:
                return True

        return False

    def parse(
        self,
        mainfile: str,
        archive: 'EntryArchive',
        logger: 'BoundLogger' = None,
        child_archives=None,
    ) -> None:
        data_file = Path(mainfile).name
        if isinstance(archive.m_context, ServerContext):
            normalized_mainfile = mainfile.replace('\\', '/')
            if '/raw/' in normalized_mainfile:
                data_file = normalized_mainfile.split('/raw/', 1)[1]
            else:
                data_file = normalized_mainfile.rsplit('/', 1)[-1]

        entry = ELNVibratingSampleMagnetometry()
        entry.data_file = data_file
        archive.data = entry
        archive.metadata.entry_name = f'{data_file} data file'
