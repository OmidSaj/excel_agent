# example.py
"""
Example script to demonstrate beam design calculations.
"""
from beam_design.calculations import (
    calculate_moment, calculate_shear, get_moment_capacity, get_shear_capacity,
    check_load, check_capacity, check_shear, get_design_status
)

def main():
    # Input parameters
    beam_length_ft = 20
    P_kip = 15
    area_load_q = 30
    trib_width_ft = 20
    section = 'delta'  # Can be 'alpha', 'bravo', 'charlie', or 'delta'
    max_P = 100

    # Section property data
    section_data = {
        'alpha': 20,    # alpha_M_kip_ft
        'bravo': 50,    # bravo_M_kip_ft
        'charlie': 100, # charlie_M_kip_ft
        'delta': 200    # delta_M_kip_ft
    }
    section_shear_capacity_map = {
        'alpha': 40,    # section_alpha_V
        'bravo': 60,    # V_bravo
        'charlie': 80,  # section_charlie_V_kip
        'delta': 150    # V_delta
    }

    # Calculations
    moment = calculate_moment(P_kip, beam_length_ft, area_load_q, trib_width_ft)
    shear = calculate_shear(P_kip, beam_length_ft, area_load_q, trib_width_ft)
    moment_capacity = get_moment_capacity(section, section_data)
    shear_capacity = get_shear_capacity(section, section_shear_capacity_map)

    load_check_message = check_load(P_kip, max_P)
    moment_capacity_status = check_capacity(moment, moment_capacity)
    shear_capacity_status = check_shear(shear, shear_capacity)
    design_status = get_design_status(moment_capacity_status, shear_capacity_status)

    # Output results
    print(f"Beam Section: {section}")
    print(f"Midspan Moment (kip-ft): {moment:.2f}")
    print(f"Shear Force (kip): {shear:.2f}")
    print(f"Moment Capacity (kip-ft): {moment_capacity}")
    print(f"Shear Capacity (kip): {shear_capacity}")
    print(f"Load Check: {load_check_message}")
    print(f"Moment Capacity Status: {moment_capacity_status}")
    print(f"Shear Capacity Status: {shear_capacity_status}")
    print(f"Design Status: {design_status}")

if __name__ == "__main__":
    main()
