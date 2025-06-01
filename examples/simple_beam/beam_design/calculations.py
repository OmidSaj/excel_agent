"""
beam_design/calculations.py
---------------------------
Contains core calculation functions for beam design checks.
"""

def calculate_moment(P_kip, beam_length_ft, area_load_q, trib_width_ft):
    """
    Calculate the maximum moment (kip-ft) on the beam.
    """
    return P_kip * beam_length_ft / 4 + (area_load_q * trib_width_ft / 1000) * beam_length_ft ** 2 / 8

def calculate_shear(P_kip, beam_length_ft, area_load_q, trib_width_ft):
    """
    Calculate the maximum shear (kip) on the beam.
    """
    return P_kip * beam_length_ft / 2 + area_load_q * trib_width_ft * beam_length_ft / 2 / 1000

def get_section_capacity(section_type, section_database):
    """
    Retrieve moment and shear capacity for a given section type.
    """
    return section_database[section_type]['M'], section_database[section_type]['V']

def check_load(P_kip, max_P):
    """
    Check if the applied load exceeds the maximum allowable load.
    """
    return "Load is too much!" if P_kip > max_P else "Load below limit"

def check_capacity(applied, capacity):
    """
    Check if the applied value is within the capacity.
    Returns 'OK' if within, 'NG' if not.
    """
    return 'OK' if capacity >= applied else 'NG'

def design_status(moment_status, shear_status):
    """
    Returns 'Pass' if both moment and shear status are OK, else 'Fail'.
    """
    return 'Pass' if (moment_status == 'OK' and shear_status == 'OK') else 'Fail'
