# Beam Design Calculator

This repository provides a simple Python implementation for basic beam design checks, including moment and shear calculations, and section capacity checks for different beam types.

## Structure

- `beam_design/calculations.py`: Core calculation functions for moment, shear, and capacity checks.
- `example.py`: Example script demonstrating how to use the calculation functions.

## Usage

1. **Clone the repository** or copy the files to your project directory.
2. Run the example script:

```bash
python example.py
```

## Calculation Details

- **Moment Calculation**: Computes the midspan moment for a simply supported beam with a point load and area load.
- **Shear Calculation**: Computes the maximum shear force for the same loading conditions.
- **Capacity Checks**: Compares calculated moment and shear with the section's capacity.
- **Design Status**: Reports if the design passes or fails based on the checks.

## Customization

You can modify the input parameters in `example.py` to suit your specific beam and loading conditions. The section properties (moment and shear capacities) can also be updated as needed.

## Example Output

```
Beam Section: delta
Midspan Moment (kip-ft): 225.00
Shear Force (kip): 180.00
Moment Capacity (kip-ft): 200
Shear Capacity (kip): 150
Load Check: Load below limit
Moment Capacity Status: NG
Shear Capacity Status: NG
Design Status: Fail
```

## License

MIT License
