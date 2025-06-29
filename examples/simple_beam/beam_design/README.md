# Beam Design Calculator

This repository provides a simple Python-based calculator for checking the moment and shear design of a simply supported beam subjected to a midspan point load and a uniform area load. The code is organized for clarity and easy extension.

## Features
- Calculates midspan moment and support shear for a simply supported beam.
- Checks the calculated moment and shear against section capacities from a predefined database.
- Provides clear pass/fail status for the design.
- Easily extensible for more section types or different loading scenarios.

## File Structure
- `beam_design/calculations.py`: Core calculation functions for moment, shear, and design checks.
- `beam_design/example.py`: Example script demonstrating how to use the calculation functions.
- `beam_design/README.md`: This documentation file.

## Usage
1. Clone or download this repository.
2. Run the example script:

```bash
cd beam_design
python example.py
```

3. Modify the input parameters in `example.py` as needed for your own beam design scenario.

## Section Database
The section database is hardcoded for demonstration and includes the following types:

| Section  | Moment Capacity (kip-ft) | Shear Capacity (kip) |
|----------|-------------------------|----------------------|
| alpha    | 20                      | 40                   |
| bravo    | 50                      | 60                   |
| charlie  | 100                     | 80                   |
| delta    | 200                     | 150                  |

## Example Output
```
Beam Design Example
==============================
Beam Length: 20 ft
Midspan Point Load: 15 kip
Area Load: 30 psf
Tributary Width: 20 ft
Section Type: delta

Calculated Moment at Midspan: 375.00 kip-ft
Calculated Shear at Support: 180.00 kip

Load is too much!

Moment Capacity: 200 kip-ft
Shear Capacity: 150 kip
Moment Capacity Status: NG
Shear Capacity Status: NG

Design Status: Fail
```

## License
MIT License
