import csv
import io
import os
import pandas as pd  # Import the pandas library

# print in which directory the script is running
print(f"Script is running in directory: {os.getcwd()}")
date_suffix = "_202501"
# POPULATION = "all"  # Set the population variable to "all"
# POPULATION = "left"  # Set the population variable to "all"
# POPULATION = "macron"  # Set the population variable to "all"
# POPULATION = "farright"  # Set the population variable to "all"
POPULATION = "absentionists"  # Set the population variable to "all"

# Provided list of names as a string
# load from names.txt
try:
    names_string = io.open("names.txt", "r", encoding="utf-8").read()
except FileNotFoundError:
    print("Error: names.txt not found in mining_ELABE directory.")
    exit()

# Provided concatenated table data as a string
# load from table.txt
try:
    table_string = io.open("table.txt", "r", encoding="utf-8").read()
except FileNotFoundError:
    print("Error: table.txt not found in mining_ELABE directory.")
    exit()


# --- Step 1: Process Names ---
# Split the names string into a list of individual names
names_list = [name.strip() for name in names_string.strip().split("\n")]
num_names = len(names_list)

# Step 1.2: Load the zeros, skipped in the table
df_zeros = pd.read_csv("zeros.csv", sep=",", encoding="utf-8")

# --- Step 2: Read and Process candidate.csv Data using pandas ---
# Read the candidate.csv file into a pandas DataFrame
try:
    candidate_df = pd.read_csv("../candidates.csv")
except FileNotFoundError:
    print("Error: candidate.csv not found. Please make sure the file is in the correct directory.")
    exit()  # Exit if the file is not found

# Create a dictionary to map full names (or name + surname) to candidate_id
candidate_map = {}
# Iterate over DataFrame rows to populate the map
for index, row in candidate_df.iterrows():
    candidate_id = row["candidate_id"].strip()
    name = row["name"].strip()
    surname = row["surname"].strip()
    full_name = f"{name} {surname}".strip()

    # Populate the candidate_map dictionary
    candidate_map[full_name] = candidate_id
    if name:
        candidate_map[name] = candidate_id
    if surname:
        candidate_map[surname] = candidate_id


# --- Step 3: Process Table Data ---
# Split the table string into a list of individual numbers
table_values = [int(value.strip()) for value in table_string.strip().split("\n")]

# Check if the number of values is consistent with the number of names and columns (N * 5)
expected_values = num_names * 5
if len(table_values) != expected_values:
    print(
        f"Warning: Expected {expected_values} values in the table data based on {num_names} names and 5 columns, "
        f"but found {len(table_values)}. The output might be incorrect."
    )

# --- Restructure the table_values based on column-by-column concatenation ---
# The input is: [col1_row1, col1_row2, ..., col1_rowN, col2_row1, ..., col5_rowN]
# We need to reshape it into: [[col1_row1, col2_row1, ..., col5_row1], ..., [col1_rowN, ..., col5_rowN]]

table_rows = []
num_columns = 5  # There are 5 intention mention columns

idx_doublets = []
for _, row in df_zeros.iterrows():
    print(row)
    idx_doublets.append((row["intention_number"] - 1, names_list.index(row["name"])))

idx_doublets_sum = [sum(x) for x in idx_doublets]

# Iterate through each row index (from 0 to num_names - 1)
offset = 0
for i in range(num_names):
    current_row = []
    # For each row, collect the value from each of the 5 columns
    for j in range(num_columns):
        # The index in the flat table_values list for the value at row i, column j is:
        # (j * num_names) + i
        # This is because all values for column j are listed consecutively first.

        if (j, i) in idx_doublets:
            current_row.append(0)
            print(f"Zero added for doublet at index ({i}, {j})")
        else:
            offset = sum(
                [
                    -1
                    for n in range(num_names)
                    for m in range(num_columns)
                    if (m, n) in idx_doublets and n + m * num_names < i + j * num_names
                ]
            )
            print(f"Offset: {offset}")
            flat_index = (j * num_names) + i + offset
            try:
                current_row.append(table_values[flat_index])
            except IndexError:
                print(f"Warning: Index {flat_index} out of bounds for table_values. Table data may be incomplete.")
                # Append a placeholder or handle as needed if data is missing
                current_row.append("")  # Append empty string for missing data

        if (i, j) in idx_doublets:
            offset -= 1

    table_rows.append(current_row)

# --- Step 4: Combine Data and Create CSV Rows ---
# Define the header for the output CSV
header = [
    "candidate_id",
    "intention_mention_1",
    "intention_mention_2",
    "intention_mention_3",
    "intention_mention_4",
    "intention_mention_5",
    "intention_mention_6",
    "intention_mention_7",
    "poll_type_id",
    "population",
]

# Create the data rows for the output CSV
output_data_rows = []
for i in range(num_names):
    # Get the name from the input list
    name_from_list = names_list[i]
    print(f"Processing candidate: {name_from_list}")
    # Find the candidate_id using the candidate_map
    # Use the full name from the list to look up in the map
    candidate_id = candidate_map.get(name_from_list)
    if candidate_id is None:
        # Check if the name from the list is a key in the map (handles potential partial matches)
        if name_from_list not in candidate_map:
            raise ValueError(
                f"Candidate ID not found for name: '{name_from_list}'. "
                f"Please check the candidate.csv file and ensure names in names.txt match entries "
                f"(full name, name, or surname)."
            )
        else:
            candidate_id = candidate_map[name_from_list]

    # Get the 5 intention mention values for the current candidate
    # Use a try-except block in case table_rows has fewer rows than names
    intention_mentions = []
    try:
        # table_rows is now correctly structured row by row
        intention_mentions = table_rows[i]
    except IndexError:
        print(f"Warning: No table data found for candidate index {i}. Skipping.")
        continue  # Skip this candidate if no table data is available

    # Ensure we have exactly 5 intention mentions, pad with empty strings if necessary
    while len(intention_mentions) < 5:
        intention_mentions.append("")

    # Add the fixed columns (intention_mention_6, intention_mention_7, poll_type_id, population)
    fixed_columns = ["", "", "pt2", POPULATION]

    # Combine all elements for the current row
    row = [candidate_id] + intention_mentions + fixed_columns
    output_data_rows.append(row)

# chek sum of intention_mention_1 to intention_mention_7 (nan are zeros)
for row in output_data_rows:
    # Convert the intention mentions to float and sum them
    intention_mentions = [float(x) if x else 0 for x in row[1:6]]  # Only the first 5 columns
    total_intentions = sum(intention_mentions)
    if total_intentions != 100:
        print(
            f"Warning: Sum of intention mentions for candidate {row[0]} is not 100. "
            f"Sum: {total_intentions}. Row data: {row}"
        )


# --- Step 5: Write to CSV File ---
output_filename = f"elabe{date_suffix}_{POPULATION}.csv"

# Ensure the output directory exists
output_dir = os.path.dirname(output_filename)
if output_dir and not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"Created directory: {output_dir}")


# Use 'w' mode for writing, newline='' is important for CSV files
with open(output_filename, "w", newline="", encoding="utf-8") as outfile:
    csv_writer = csv.writer(outfile)

    # Write the header row
    csv_writer.writerow(header)

    # Write the data rows
    csv_writer.writerows(output_data_rows)

print(f"Successfully generated {output_filename}")
print("Note: Acronyms were mapped using the provided candidate.csv data via pandas.")
