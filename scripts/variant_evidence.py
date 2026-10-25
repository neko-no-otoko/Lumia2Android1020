#!/usr/bin/env python3
"""Consistency gates for attributed exact-image comparisons, not raw verification.

No proprietary payload or disassembly is imported. The raw inputs remain private
on the authorized Mini; this validates recorded scope, not vendor authenticity.
"""
import re

REFERENCE_SHA = '200c402351e7b488fd320bc944a7ab8f1dde2522eac5e7c203584852f541ef08'
TARGET_SHA = '26b69b84a0e5e529f8dcb696c43625a040e79fa3ec3e96fc7328a7c9bd6faa97'
TARGET_LOADERS = {
    'BOOTARM.EFI': '3e0a832f8d4f8971b31ada5d20b280d1be33d47404f97b367731ee6e21b0b8bc',
    'winload.efi': '187f21bdd129167cca9e7dd78dd8d60b8733e752a905f7b07d657e56a751b10e',
}


def validate(record):
    if record['schema'] != 1 or record['comparison_scope'] != 'two_exact_ffus':
        raise ValueError('Exact comparison scope cannot imply all-variant equivalence')
    target = record['target']
    if record['reference_ffu_sha256'] != REFERENCE_SHA or target['ffu_sha256'] != TARGET_SHA:
        raise ValueError('Unexpected exact FFU pair')
    if (target['rm'] != 'RM-877' or target['product_code'] != '059T019'
            or target['platform'] != 'Nokia.MSM8960.P5217_ATT'
            or target['ffu_bytes'] != 1684013056 or target['chunk_hashes_passed'] != 12844
            or target['ffu_crc32'] != '7346f0cb' or target['vendor_signature_trust'] != 'unverified'):
        raise ValueError('Unreviewed target identity/integrity claim')
    for value in record['target_loader_sha256'].values():
        if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
            raise ValueError('Malformed loader fingerprint')
    if record['target_loader_sha256'] != TARGET_LOADERS:
        raise ValueError('Direct target loader findings require their exact fingerprints')
    assets = record['byte_identical_assets']
    if (assets['plat_acpi_file_count'] != 12 or assets['external_panel_xml'] != 'PTANYA.XML'
            or assets['pep_device_packages'] != 35 or assets['pep_action_groups'] != 418
            or assets['pep_clock_names'] != 72):
        raise ValueError('Unreviewed selected-asset comparison')
    modules = record['selected_uefi_modules']
    if (modules['compared'] != 14 or modules['different'] != 13
            or modules['whole_file_identical'] != ['PmicDxe']
            or modules['general_behavior_equivalence'] != 'unverified'):
        raise ValueError('Changed UEFI requires direct review of each claimed behavior')
    drivers = record['drivers']
    if (drivers['pmic_gpio']['comparison'] != 'whole_file_identical'
            or drivers['pep']['comparison'] != 'declared_raw_sections_identical_whole_file_differs'
            or drivers['touch']['comparison'] != 'executable_sections_identical_rdata_pdata_differ'
            or drivers['touch']['configuration_carry_forward'] is not False
            or drivers['touch']['compared_registry_settings'] != 'unchanged_except_package_identity_path_version'):
        raise ValueError('Executable-only equality cannot carry changed touch data')
    loader = record['target_loader_review']
    if (loader['override']['bcd_inspected'] is not False
            or loader['override']['actual_option_root_values'] != 'unobserved'
            or loader['graphics']['stock_initialization_passive'] is not False
            or loader['graphics']['live_mode_observed'] is not False
            or loader['live_observer_route_accepted'] is not False
            or loader['live_observer_execution_authorized'] is not False):
        raise ValueError('Static loader tracing cannot become runtime BCD/GOP evidence or observer approval')
    if (record['installed_runtime_tables_observed'] is not False
            or record['runtime_product_dat_observed'] is not False
            or record['target_configuration_emitted'] is not False):
        raise ValueError('Static comparison does not establish runtime state or target configuration')
    return dict(result='PASS', comparison_scope='two_exact_ffus', target_rm='RM-877',
                target_product_code=target['product_code'], target_ffu_sha256=target['ffu_sha256'],
                table_resource_facts='corroborated for this exact target image',
                pmic_decoder='whole-file equality', pep_decoder='declared raw-section equality corroborates static decoder',
                touch_configuration='selected registry settings directly compared unchanged; other data not inherited',
                target_loader_review='bounded static pass complete; no runtime BCD/GOP/EFI observations',
                general_uefi_behavior='unverified',
                signature_trust='unverified', runtime_enablement='none')
