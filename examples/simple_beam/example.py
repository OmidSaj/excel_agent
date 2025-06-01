"""
example.py
----------
Example script to demonstrate beam design calculations.
"""

from beam_design.calculations import (
    calculate_moment, calculate_shear, get_section_capacity,
    check_load, check_capacity, design_status
)
from beam_design.section_database import SECTION_DATABASE, MAX_P

# Example input values
beam_length_ft = 20
P_kip = 15
area_load_q = 30
trib_width_ft = 20
section_type = 'delta'  # Can be 'alpha', 'bravo', 'charlie', or 'delta'

# Calculations
moment = calculate_moment(P_kip, beam_length_ft, area_load_q, trib_width_ft)
shear = calculate_shear(P_kip, beam_length_ft, area_load_q, trib_width_ft)
moment_capacity, shear_capacity = get_section_capacity(section_type, SECTION_DATABASE)

load_message = check_load(P_kip, MAX_P)
moment_status = check_capacity(moment, moment_capacity)
shear_status = check_capacity(shear, shear_capacity)
design_result = design_status(moment_status, shear_status)

print(f"Beam Design Example\n{'='*20}")
print(f"Section Type: {section_type}")
print(f"Beam Length: {beam_length_ft} ft")
print(f"Point Load: {P_kip} kip")
print(f"Area Load: {area_load_q} psf")
print(f"Tributary Width: {trib_width_ft} ft")
print(f"\nCalculated Moment: {moment:.2f} kip-ft")
print(f"Calculated Shear: {shear:.2f} kip")
print(f"Moment Capacity: {moment_capacity} kip-ft [{moment_status}]")
print(f"Shear Capacity: {shear_capacity} kip [{shear_status}]")
print(f"\nLoad Check: {load_message}")
print(f"Design Status: {design_result}")
