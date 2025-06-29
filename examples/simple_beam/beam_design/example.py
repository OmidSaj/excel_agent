"""
beam_design/example.py
----------------------
Example script to demonstrate beam design calculations.
"""
from calculations import calculate_moment, calculate_shear, get_section_properties, check_load, check_capacity

def main():
    # Example input values
    length_of_beam_ft = 20
    P_kip = 15
    area_load_q = 30
    trib_width_ft = 20
    section_type = 'delta'  # Can be 'alpha', 'bravo', 'charlie', or 'delta'
    max_P = 100

    # Calculations
    moment = calculate_moment(P_kip, length_of_beam_ft, area_load_q, trib_width_ft)
    shear = calculate_shear(P_kip, length_of_beam_ft, area_load_q, trib_width_ft)
    load_message = check_load(P_kip, max_P)
    capacity_results = check_capacity(moment, shear, section_type)

    # Output results
    print(f"Beam Design Example\n{'='*30}")
    print(f"Beam Length: {length_of_beam_ft} ft")
    print(f"Midspan Point Load: {P_kip} kip")
    print(f"Area Load: {area_load_q} psf")
    print(f"Tributary Width: {trib_width_ft} ft")
    print(f"Section Type: {section_type}")
    print(f"\nCalculated Moment at Midspan: {moment:.2f} kip-ft")
    print(f"Calculated Shear at Support: {shear:.2f} kip")
    print(f"\n{load_message}")
    print(f"\nMoment Capacity: {capacity_results['moment_capacity_Mcap']} kip-ft")
    print(f"Shear Capacity: {capacity_results['shear_capacity_Vcap']} kip")
    print(f"Moment Capacity Status: {capacity_results['moment_capacity_status']}")
    print(f"Shear Capacity Status: {capacity_results['shear_capacity_status']}")
    print(f"\nDesign Status: {capacity_results['design_status']}")

if __name__ == "__main__":
    main()
