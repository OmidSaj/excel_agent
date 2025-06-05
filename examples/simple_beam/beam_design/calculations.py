# beam_design/calculations.py
"""
This module contains functions for beam design calculations including moment, shear, and capacity checks.
"""

def calculate_moment(P_kip, beam_length_ft, area_load_q, trib_width_ft):
    """
    Calculate the moment at mid span in kip-feet.
    """
    moment = P_kip * beam_length_ft / 4 + (area_load_q * trib_width_ft / 1000) * beam_length_ft ** 2 / 8
    return moment

def calculate_shear(P_kip, beam_length_ft, area_load_q, trib_width_ft):
    """
    Calculate the shear force V in kips.
    """
    shear = P_kip * beam_length_ft / 2 + area_load_q * trib_width_ft * beam_length_ft / 2 / 1000
    return shear

def get_moment_capacity(section, section_data):
    """
    Get the moment capacity for the selected section.
    """
    return section_data[section]

def get_shear_capacity(section, section_shear_capacity_map):
    """
    Get the shear capacity for the selected section.
    """
    return section_shear_capacity_map[section]

def check_load(P_kip, max_P):
    """
    Check if the load P exceeds the maximum allowable load.
    """
    return "Load is too much!" if P_kip > max_P else "Load below limit"

def check_capacity(moment, moment_capacity):
    """
    Check if the moment capacity is sufficient.
    """
    return 'OK' if moment_capacity >= moment else 'NG'

def check_shear(shear, shear_capacity):
    """
    Check if the shear force is within the shear capacity.
    """
    return 'OK' if shear <= shear_capacity else 'NG'

def get_design_status(moment_status, shear_status):
    """
    Determine the overall design status.
    """
    return 'Fail' if (moment_status == 'NG' or shear_status == 'NG') else 'Pass'
