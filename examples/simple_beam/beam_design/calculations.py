"""
beam_design/calculations.py
---------------------------
Contains core calculation functions for beam design checks.
"""

def calculate_moment(P_kip, length_of_beam_ft, area_load_q, trib_width_ft):
    """
    Calculate the moment at mid span of the beam (kip-ft).
    """
    uniform_load_kip_ft = area_load_q * trib_width_ft / 1000  # psf * ft / 1000 = kip/ft
    M = P_kip * length_of_beam_ft / 4 + uniform_load_kip_ft * length_of_beam_ft ** 2 / 8
    return M

def calculate_shear(P_kip, length_of_beam_ft, area_load_q, trib_width_ft):
    """
    Calculate the shear force at the support (kips).
    """
    uniform_load_kip_ft = area_load_q * trib_width_ft / 1000
    V = P_kip * length_of_beam_ft / 2 + uniform_load_kip_ft * length_of_beam_ft / 2
    return V

def get_section_properties(section_type):
    """
    Return moment and shear capacity for a given section type.
    """
    section_database = {
        'alpha': {'M': 20, 'V': 40},
        'bravo': {'M': 50, 'V': 60},
        'charlie': {'M': 100, 'V': 80},
        'delta': {'M': 200, 'V': 150}
    }
    return section_database.get(section_type, None)

def check_load(P_kip, max_P):
    return "Load is too much!" if P_kip > max_P else "Load below limit"

def check_capacity(moment, shear, section_type):
    props = get_section_properties(section_type)
    if props is None:
        raise ValueError(f"Unknown section type: {section_type}")
    moment_status = 'OK' if props['M'] >= moment else 'NG'
    shear_status = 'OK' if props['V'] >= shear else 'NG'
    design_status = 'Fail' if (moment_status == 'NG' or shear_status == 'NG') else 'Pass'
    return {
        'moment_capacity_status': moment_status,
        'shear_capacity_status': shear_status,
        'design_status': design_status,
        'moment_capacity_Mcap': props['M'],
        'shear_capacity_Vcap': props['V']
    }
