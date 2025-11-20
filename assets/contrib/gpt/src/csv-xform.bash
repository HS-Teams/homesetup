#!/usr/bin/env bash
# csv-xform.bash
# Purpose: Transform an N-column CSV into an X by Y matrix, supporting piped input or file input

VERSION="1.0.0" # https://semver.org/ ; major.minor.patch

# Display usage information
usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS] [<input_file>] <output_columns>

Transform an N-column CSV into a grid format with a specified number of output columns.
Both input and output columns must be even numbers.

The script can accept input in two ways:
  1. From a file specified as <input_file>.
  2. From piped input, e.g., echo "1234,4567,7890,asdf,fghj,jklk" | $0 <output_columns>

Arguments:
  <input_file>         Path to the input CSV file with an even number of columns.
                       This argument is optional if input is piped.
  <output_columns>     Desired number of columns in the output (must be an even number).

Options:
  -o, --outfile FILE   Specify an output file to save the transformed data (default: stdout).
  -h, --help           Display this help message and exit.
  -v, --version        Display the script version and exit.

Examples:
  $(basename "$0") Icons.csv 4               # Transform Icons.csv into a 4-column format and print to stdout.
  $(basename "$0") -o output.csv Icons.csv 4 # Transform Icons.csv into a 4-column format and save to output.csv.
  echo "1234,4567,7890,asdf,fghj,jklk" | $(basename "$0") 4  # Pipe comma-separated values and transform into 4 columns.

EOF
    exit 1
}

# Display version information
version() {
    echo "$0 version $VERSION"
    exit 0
}

# Validate input arguments and file
validate_input() {
    local input_file="$1"
    local output_columns="$2"

    # Check if output columns is an even number
    if (( output_columns % 2 != 0 )); then
        echo "ERROR: The output column count must be an even number."
        exit 1
    fi

    # Determine input columns from piped data or file
    if [[ -n "$input_file" ]]; then
        if [[ ! -f "$input_file" ]]; then
            echo "ERROR: File '$input_file' not found."
            exit 1
        fi
        input_columns=$(head -n 1 "$input_file" | awk -F',' '{print NF}')
    else
        # Read entire piped input to determine columns
        piped_data=$(cat)
        if [[ -z "$piped_data" ]]; then
            echo "ERROR: No input data provided."
            exit 1
        fi
        input_columns=$(echo "$piped_data" | awk -F',' '{print NF}')
        # Save piped data to a temporary file for processing
        echo "$piped_data" > /tmp/csv-xform-input.tmp
        input_file="/tmp/csv-xform-input.tmp"
    fi

    # Check if input columns is an even number
    if (( input_columns % 2 != 0 )); then
        echo "ERROR: The input column count must be an even number."
        exit 1
    fi

    # Check if input_columns was correctly set
    if (( input_columns == 0 )); then
        echo "ERROR: Input data appears to be empty or invalid."
        exit 1
    fi

    # Warn if output columns is not a multiple of input columns
    if (( output_columns % input_columns != 0 )); then
        echo "WARNING: Output columns are not a multiple of input columns. Results may not be as expected."
    fi
}

# Process the CSV data and reformat it into the desired output
process_csv() {
    local output_columns="$1"
    local output_file="$2"
    local input_source="$3"

    awk -v input_cols="$input_columns" -v output_cols="$output_columns" -F',' '
    {
        for (i = 1; i <= NF; i++) {
            data[count++] = $i
        }
    }
    END {
        for (i = 0; i < count; i++) {
            printf "%s", data[i]
            if ((i + 1) % output_cols == 0) {
                printf "\n"
            } else {
                printf ","
            }
        }
        # Print final newline if not added
        if (count % output_cols != 0) {
            printf "\n"
        }
    }
    ' "$input_source" > "${output_file:-/dev/stdout}"
}

# Main function to orchestrate the script
main() {
    local output_file=""
    local input_file=""

    # Parse options
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -o|--outfile)
                output_file="$2"
                shift 2
                ;;
            -h|--help)
                usage
                ;;
            -v|--version)
                version
                ;;
            -*)
                echo "Invalid option: $1" >&2
                usage
                ;;
            *)
                break
                ;;
        esac
    done

    # Determine if input is piped or from a file
    if [[ -p /dev/stdin ]]; then
        # Data is piped; set input_file to empty
        input_file=""
        output_columns="$1"
    else
        # Data is not piped; expect input_file as argument
        input_file="$1"
        output_columns="$2"
        shift 2
    fi

    # Validate inputs
    validate_input "$input_file" "$output_columns"

    # Process and transform CSV data
    process_csv "$output_columns" "$output_file" "${input_file:-/tmp/csv-xform-input.tmp}"

    # Clean up temporary file if created
    [[ -f /tmp/csv-xform-input.tmp ]] && rm /tmp/csv-xform-input.tmp
}

# Execute the main function
main "$@"

exit 0
