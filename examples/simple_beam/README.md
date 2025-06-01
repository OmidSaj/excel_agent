# Beam Design Example

This repository provides a simple, modular Python implementation for basic beam design checks. It demonstrates how to calculate the maximum moment and shear for a simply supported beam with a mid-span point load and a distributed area load, and how to check these against section capacities from a database.

## Directory Structure

```
beam_design/
    calculations.py         # Core calculation functions
    section_database.py     # Section property database
example.py                 # Example script to run the calculations
```

## How to Use

1. **Clone or download this repository.**
2. **Run the example script:**

   ```bash
   python example.py
   ```

   This will print out the results of the beam design check for the example values provided in `example.py`.

## Customization

- To use different beam or load parameters, edit the variables at the top of `example.py`.
- To add or modify section properties, edit the `SECTION_DATABASE` dictionary in `beam_design/section_database.py`.

## Calculation Details

- **Moment and Shear:**
  - Moment is calculated as:
    \[ M = \frac{P \cdot L}{4} + \frac{q \cdot w \cdot L^2}{8 \cdot 1000} \]
    where `P` is the point load (kip), `L` is the span (ft), `q` is the area load (psf), and `w` is the tributary width (ft).
  - Shear is calculated as:
    \[ V = \frac{P \cdot L}{2} + \frac{q \cdot w \cdot L}{2 \cdot 1000} \]
- **Capacity Checks:**
  - The script checks if the calculated moment and shear are within the section's capacity.
  - If either check fails, the design status is 'Fail'.

## Example Output

```
Beam Design Example
====================
Section Type: delta
Beam Length: 20 ft
Point Load: 15 kip
Area Load: 30 psf
Tributary Width: 20 ft

Calculated Moment: 112.00 kip-ft
Calculated Shear: 37.00 kip
Moment Capacity: 200 kip-ft [OK]
Shear Capacity: 150 kip [OK]

Load Check: Load below limit
Design Status: Pass
```

## License

This code is provided for educational and demonstration purposes.
