# Entity Resolution Analyzer

This project is a Python-based tool for matching and resolving company entities from datasets. It uses fuzzy string matching and heuristic-based scoring across various data points (such as company name, country, city, street, and email) to determine the best match between an input entity and a set of candidate entities.

## Features

- **Fuzzy Matching:** Utilizes `rapidfuzz` for robust string similarity comparisons of company names and locations.
- **Data Cleaning:** Automatically normalizes strings, standardizes company suffixes (e.g., INC, LLC, GMBH), and handles missing values.
- **Multi-Factor Scoring:** Calculates a weighted overall match score based on:
  - Company Name (45%)
  - Country (25%)
  - City (15%)
  - Location Details like Street or Postcode (15%)
- **Penalties:** Applies score penalties for mismatches in critical fields (like country) or generic email domains (e.g., gmail.com, yahoo.com).

## Prerequisites

The script requires Python 3 and the following libraries:

- `pandas`
- `rapidfuzz`
- `numpy`

You can install the required dependencies using pip:

```bash
pip install pandas rapidfuzz numpy
```

## Usage

You can run the script via the command line. It accepts several arguments to customize the input/output files and the matching threshold.

```bash
python analyse.py [options]
```

### Arguments

- `-i`, `--inputFile`: Path to the input CSV file. (Default: `presales_data_sample.csv`)
- `-o`, `--outputFile`: Path to the output summary CSV file. (Default: `resolved_entities_summary.csv`)
- `-s`, `--scoreThreshold`: The minimum score (0-100) required to consider a match successful. (Default: `70.0`)
- `-u`, `--unresolvedFile`: (Optional) Path to save entities that failed to meet the matching threshold. If not provided, unresolved entities are not saved separately.

### Example

```bash
python analyse.py -i my_dataset.csv -o results.csv -s 75.0 -u unresolved_cases.csv
```

## Input File Format

The script expects the input CSV file to contain specific columns, grouped by `input_row_key`, where each group represents one input entity and multiple candidate entities to match against.

Expected columns include:
- `input_row_key`: Unique identifier for the input entity.
- `input_company_name`: The name of the company being searched.
- `company_name`: Candidate company name.
- `company_legal_names` / `company_commercial_names`: Alternative names for candidates (pipe `|` separated).
- `input_main_country_code` / `main_country_code`: Country codes.
- `locations` / `num_locations`: Additional location data for candidates.
- `input_main_city` / `main_city`: City names.
- `input_main_postcode` / `main_postcode`: Postal codes.
- `input_main_street` / `main_street`: Street addresses.
- `primary_email`: Candidate's email address.
- `veridion_id`: The unique identifier of the candidate entity.

## Output

1. **Terminal Output:** The script prints the processing status for each `input_row_key`, displaying the calculated scores for each candidate, color-coded for quick visual inspection (Green for matched, Red for unmatched).
2. **Output CSV (`--outputFile`):** A summary containing the `input_row_key`, `input_company_name`, the matched `veridion_id` (if any), the final match score, and the match status.
3. **Unresolved CSV (`--unresolvedFile`):** (If specified) Contains the full original rows for inputs that did not find a candidate meeting the required threshold.
