from typing import TYPE_CHECKING

import numpy as np
from nomad.datamodel.data import ArchiveSection, EntryData
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.metainfo import Quantity, Section, SubSection

from readers_ientrance import read_lakeshore_vsm
from .base_schema import m_package, BaseMagnetometry, MagnetometrySample, MagnetometryResult

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger


# --- 1. VSM-Specific Subsections ---

class FieldConfigurations(ArchiveSection):
    magnet_model = Quantity(type=str)
    power_supply = Quantity(type=str)
    magnet_mode = Quantity(type=str)
    head_amplitude = Quantity(type=str)
    gap_settings = Quantity(type=str)
    coil_set_name = Quantity(type=str)
    coil_set_serial_number = Quantity(type=str)
    coil_set_balance_number = Quantity(type=np.float64)
    moment_x_calibration_value = Quantity(type=np.float64, description='emu/volt')
    moment_x_calibration_field = Quantity(type=np.float64, description='Oe')
    moment_x_calibration_expected_moment = Quantity(type=np.float64, description='emu')
    moment_x_calibration_standard_id = Quantity(type=str)
    moment_x_calibration_comments = Quantity(type=str)


class AdvancedAcquisitionSetup(ArchiveSection):
    acquisition_mode = Quantity(type=str)
    pause_at_plus_minus_max_fields = Quantity(type=np.float64, unit='s')
    moment_meter_range_mode = Quantity(type=str)
    gaussmeter_range_mode = Quantity(type=str)
    gaussmeter_fixed_range = Quantity(type=str)


class AcquisitionSetup(ArchiveSection):
    saturation_field = Quantity(type=str)
    max_field = Quantity(type=str)
    forc_type = Quantity(type=str)
    max_hc_field = Quantity(type=np.float64, description='Oe')
    max_hu_field = Quantity(type=np.float64, description='Oe')
    min_hu_field = Quantity(type=np.float64, description='Oe')
    calibration_field_tolerance = Quantity(type=str)
    pause_at_calibration_field = Quantity(type=np.float64, unit='s')
    number_of_forcs = Quantity(type=np.int32)
    saturation_field_tolerance = Quantity(type=str)
    pause_at_saturation_field = Quantity(type=np.float64, unit='s')
    reversal_field_tolerance = Quantity(type=str)
    pause_at_reversal_fields = Quantity(type=np.float64, unit='s')
    enable_subtract_last_branches = Quantity(type=bool)
    last_branch_iterations = Quantity(type=np.int32)
    field_step_size = Quantity(type=np.float64, description='Oe')
    include_initial_curve = Quantity(type=bool)
    averaging_time = Quantity(type=np.float64, unit='s')
    show_forc_diagram_on_the_fly = Quantity(type=bool)
    smoothing_factor = Quantity(type=np.float64)
    rotate_45_degrees = Quantity(type=bool)
    truncate_for_a_rectangle_diagram = Quantity(type=bool)
    number_of_contours = Quantity(type=np.int32)
    correct_for_drift = Quantity(type=bool)
    advanced_acquisition_setup = SubSection(sub_section=AdvancedAcquisitionSetup)


class DisplaySetup(ArchiveSection):
    x_axis = Quantity(type=str)
    left_y_axis = Quantity(type=str)
    right_y_axis = Quantity(type=str)


# --- 2. Main VSM Schema ---

class ELNVibratingSampleMagnetometry(BaseMagnetometry, EntryData):
    m_def = Section(label='Lake Shore VSM')
    data_file = Quantity(
        type=str,
        a_eln=ELNAnnotation(component=ELNComponentEnum.FileEditQuantity),
    )

    field_configurations = SubSection(sub_section=FieldConfigurations)
    acquisition_setup = SubSection(sub_section=AcquisitionSetup)
    display_setup = SubSection(sub_section=DisplaySetup)

    def _get_cleaners(self, metadata):
        """Returns cleaning utilities for the mapping process."""

        def clean_float(key, strip_str=None):
            val = metadata.get(key)
            if val:
                if strip_str:
                    val = val.replace(strip_str, '')
                try:
                    return float(val.strip())
                except ValueError:
                    return None
            return None

        def clean_int(key):
            val = metadata.get(key)
            if val:
                try:
                    return int(val.strip())
                except ValueError:
                    return None
            return None

        def clean_bool(key):
            val = metadata.get(key, '').strip().lower()
            return val == 'true' if val in ['true', 'false'] else None

        return clean_float, clean_int, clean_bool

    def _map_acquisition_and_display(self, metadata, cleaners):
        """Maps acquisition and display setups."""
        cf, ci, cb = cleaners

        acq = AcquisitionSetup()
        acq.saturation_field = metadata.get('Saturation field')
        acq.max_field = metadata.get('Max field')
        acq.forc_type = metadata.get('FORC type')
        acq.max_hc_field = cf('Max Hc field', 'Oe')
        acq.max_hu_field = cf('Max Hu field', 'Oe')
        acq.min_hu_field = cf('Min Hu field', 'Oe')
        acq.calibration_field_tolerance = metadata.get('Calibration field tolerance')
        acq.pause_at_calibration_field = cf('Pause at calibration field', 's')
        acq.number_of_forcs = ci('Number of FORCs')
        acq.saturation_field_tolerance = metadata.get('Saturation field tolerance')
        acq.pause_at_saturation_field = cf('Pause at saturation field', 's')
        acq.reversal_field_tolerance = metadata.get('Reversal field tolerance')
        acq.pause_at_reversal_fields = cf('Pause at reversal fields', 's')
        acq.enable_subtract_last_branches = cb('Enable subtract Last branches')
        acq.last_branch_iterations = ci('Last branch iterations')
        acq.field_step_size = cf('Field_step size', 'Oe')
        acq.include_initial_curve = cb('Include initial curve')
        acq.averaging_time = cf('Averaging time', 's')
        acq.show_forc_diagram_on_the_fly = cb('Show FORC diagram on the fly')
        acq.smoothing_factor = cf('Smoothing factor')
        acq.rotate_45_degrees = cb('Rotate 45 degrees')
        acq.truncate_for_a_rectangle_diagram = cb('Truncate for a rectangle diagram')
        acq.number_of_contours = ci('Number of contours')
        acq.correct_for_drift = cb('Correct for drift')

        adv = AdvancedAcquisitionSetup()
        adv.acquisition_mode = metadata.get('Acquisition mode')
        adv.pause_at_plus_minus_max_fields = cf('Pause at +/- max fields', 's')
        adv.moment_meter_range_mode = metadata.get('Moment meter range mode')
        adv.gaussmeter_range_mode = metadata.get('Gaussmeter range mode')
        adv.gaussmeter_fixed_range = metadata.get('Gaussmeter fixed range')
        acq.advanced_acquisition_setup = adv
        self.acquisition_setup = acq

        ds = DisplaySetup()
        ds.x_axis = metadata.get('X axis')
        ds.left_y_axis = metadata.get('Left Y axis')
        ds.right_y_axis = metadata.get('Right Y axis')
        self.display_setup = ds

    def _map_sample_and_configs(self, metadata, cleaners):
        """Maps sample settings to base MagnetometrySample and VSM-specific field configs."""
        cf, _, _ = cleaners

        # Map VSM Specific configurations
        fc = FieldConfigurations()
        fc.magnet_model = metadata.get('Magnet')
        fc.power_supply = metadata.get('Power supply')
        fc.magnet_mode = metadata.get('Magnet mode')
        fc.head_amplitude = metadata.get('Head amplitude')
        fc.gap_settings = metadata.get('Gap settings')
        fc.coil_set_name = metadata.get('Coil set name')
        fc.coil_set_serial_number = metadata.get('Coil set serial number')
        fc.coil_set_balance_number = cf('Coil set balance number')
        fc.moment_x_calibration_value = cf('Moment X calibration value', 'emu/volt')
        fc.moment_x_calibration_field = cf('Moment X calibration field', 'Oe')
        fc.moment_x_calibration_expected_moment = cf(
            'Moment X calibration expected moment', 'emu'
        )
        fc.moment_x_calibration_standard_id = metadata.get(
            'Moment X calibration standard ID'
        )
        fc.moment_x_calibration_comments = metadata.get('Moment X calibration comments')
        self.field_configurations = fc

        # Map Sample to Base Schema
        if not self.sample_setup:
            self.sample_setup = MagnetometrySample()

        self.sample_setup.sample_id = metadata.get('ID')
        self.sample_setup.volume = cf('Volume', 'cm³')
        self.sample_setup.area = cf('Area', 'cm²')
        self.sample_setup.mass = cf('Mass', 'g')
        self.sample_setup.density = cf('Density', 'g/cm³')
        self.sample_setup.thickness = cf('Thickness', 'mm')
        self.sample_setup.demagnetizing_factor = cf('Demagnetization factor in SI')
        self.sample_setup.demagnetizing_factor_cgs = cf('Demagnetization factor in cgs')

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger'):
        if not self.data_file:
            super().normalize(archive, logger)
            return

        try:
            with archive.m_context.raw_file(self.data_file) as file:
                vsm_data = read_lakeshore_vsm(file.name)

            cleaners = self._get_cleaners(vsm_data.metadata)

            # Map to BaseMagnetometry fields
            self.software_version = vsm_data.metadata.get('Software Version')
            self.start_time = vsm_data.metadata.get('START TIME')
            self.finish_time = vsm_data.metadata.get('FINISH TIME')
            self.measurement_type = vsm_data.metadata.get('Measurement Type')

            # Map the subsections
            self._map_sample_and_configs(vsm_data.metadata, cleaners)
            self._map_acquisition_and_display(vsm_data.metadata, cleaners)

            # Map Results to Base Schema
            if not self.results:
                self.results = [MagnetometryResult()]

            res = self.results[0]
            res.step_array = vsm_data.step
            res.iteration_array = vsm_data.iteration
            res.segment_array = vsm_data.segment
            res.magnetic_field = vsm_data.magnetic_field
            res.magnetic_moment = vsm_data.magnetic_moment
            res.time_stamp = vsm_data.time_stamp
            res.field_status = vsm_data.field_status
            res.moment_status = vsm_data.moment_status

        except Exception as e:
            logger.error(f'Error parsing VSM file: {e}')

        super().normalize(archive, logger)