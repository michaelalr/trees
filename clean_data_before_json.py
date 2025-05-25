import ast
import os
import re

import numpy as np
import pandas as pd


def select_images(df, n):
    # Load or use existing dataframe
    df = df.copy()  # Ensure original df is not modified

    # Separate matched and non-matched cases
    matched = df[df["tree_id"].notna()]  # Rows where a match exists
    non_matched = df[df["tree_id"].isna()]  # Rows where no match exists
    # matched["best_angle_diff"] = matched["best_angle_diff"].astype(float)
    # non_matched["best_angle_diff"] = non_matched["best_angle_diff"].astype(float)

    # Convert 'best_angle_diff' to numeric (force errors to NaN)
    # matched.loc[:, "best_angle_diff"] = pd.to_numeric(matched["best_angle_diff"], errors="coerce")
    # non_matched.loc[:, "best_angle_diff"] = pd.to_numeric(non_matched["best_angle_diff"], errors="coerce")
    # # Handle NaN values in 'additional_matches' column
    # non_matched.loc[:, "additional_matches"] = non_matched["additional_matches"].apply(
    #     lambda x: x if isinstance(x, list) else [])

    # Compute quantiles for best_angle_diff
    matched_high_threshold = matched["best_angle_diff"].quantile(0.9)  # Top 10%
    matched_low_threshold = matched["best_angle_diff"].quantile(0.1)  # Bottom 10%

    # Prioritize interesting matched cases
    matched_interesting = matched[
        (matched["matched_details"].apply(
            lambda x: isinstance(x, dict) and x.get("second_best_match_tree") is not None)) |
        (matched["best_angle_diff"] > matched_high_threshold) |
        (matched["best_angle_diff"] < matched_low_threshold)
        ]

    # Select 50 unique images from matched and 50 from non-matched
    selected_matched_images = matched_interesting["file_name"].drop_duplicates().sample(n=100, random_state=42)

    # # Ensure 'file_name' column exists
    # if "file_name" not in non_matched_interesting.columns:
    #     print("Column 'file_name' does not exist in non_matched_interesting")
    # Check the number of available unique images
    unique_files = non_matched["file_name"].drop_duplicates()
    if unique_files.empty:
        print("No available images to sample from.")
        selected_non_matched_images = pd.Series(dtype=object)
    else:
        sample_size = min(n, len(unique_files))  # Ensure we don't sample more than available
        selected_non_matched_images = unique_files.sample(n=sample_size, random_state=42)

    # selected_non_matched_images = non_matched_interesting["file_name"].drop_duplicates().sample(n=50, random_state=42)

    # Combine selected images
    selected_images = pd.concat([selected_matched_images, selected_non_matched_images])

    # Get all rows that belong to the selected images
    selected_df = df[df["file_name"].isin(selected_images)]

    # Save to CSV or Parquet
    selected_df.to_csv("selected_images.csv", index=False)

    return selected_df


def update_df_with_min_angle_diff(df, min_threshold=20, second_threshold=30, is_small_survey=False):
    # Create a copy to avoid modifying the original dataframe
    updated_df = df.copy()

    # Group by 'file_name' and 'tree_id' to process each combination
    grouped = updated_df.groupby(['file_name', 'tree_id'])
    counter = 0
    # Iterate over the groups
    for (file_name, tree_id), group in grouped:
        # Sort the group by best_angle_diff
        sorted_group = group.sort_values(by='best_angle_diff')

        # Get the minimum and second minimum best_angle_diff values
        if len(sorted_group) > 1:
            min_angle_diff = sorted_group.iloc[0]['best_angle_diff']
            second_min_angle_diff = sorted_group.iloc[1]['best_angle_diff']
        else:
            min_angle_diff = sorted_group.iloc[0]['best_angle_diff']
            second_min_angle_diff = float('inf')  # No second value available

        # Check if conditions are met
        # if min_angle_diff < min_threshold and second_min_angle_diff > second_threshold:
        #     min_distance_idx = sorted_group.index[0]
        # else:
        #     min_distance_idx = None  # No valid match
        min_distance_idx = sorted_group.index[0]

        # Get all indices of the group
        group_indices = group.index

        # Define the numeric columns that should get np.nan
        numeric_cols = ['tree_id', 'x_tree', 'y_tree', 'best_angle_diff']

        # Define the string columns that should get "None"
        if is_small_survey:
            string_cols = ['tree_name', 'tree_name_code', 'tree_name_big_csv']
        else:
            string_cols = ['tree_name', 'name_eng', 'name_heb', 'type_1', 'type_2', 'type_3']

        # Set fields to 'None' for rows not meeting the criteria
        for idx in group_indices:
            if idx != min_distance_idx:
                updated_df.loc[idx, numeric_cols] = np.nan  # Assign NaN to numeric columns
                updated_df.loc[idx, string_cols] = "None"  # Assign "None" to string columns
        # print(counter)
        counter += 1

    return updated_df


def fix_and_eval(value):
    if pd.isna(value):  # handles np.nan, None, etc.
        return None

    if isinstance(value, str):
        value = value.strip()  # Remove extra spaces
        value = value.replace("nan", "None")  # Replace 'nan' with 'None'
        value = re.sub(r"}\s*{", "}, {", value)  # Fix missing commas between dictionaries (handles newlines & spaces)
        try:
            return ast.literal_eval(value)  # Convert string to Python object
        except SyntaxError as e:
            print("Error parsing:", value)  # Debug print
            return None  # Return None for problematic values
    return value  # Return as is if not a string


def get_subset_df(df, table_name, n, images_list):
    # Step 1: Randomly choose 100 unique file_names
    sample_file_names = df["file_name"].drop_duplicates().sample(n=n, random_state=42)
    # Step 2: Subset the original DataFrame to only include those file_names
    df_subset = df[df["file_name"].isin(sample_file_names)]

    # Remove the extension from the original file
    base_name = os.path.splitext(table_name)[0]
    # Create the new filename
    new_filename = f"{n}_{base_name}.csv"

    # Save to CSV
    df_subset.to_csv(new_filename, index=False)
    df_subset["file_name"].to_csv(images_list, index=False, header=False)

    return df_subset


def save_file_names_to_txt(df, output_path):
    with open(output_path, "w") as f:
        for name in df["file_name"]:
            f.write(f"{name}\n")


def clean_df(df, is_small_survey=False):
    # df_non_nan_tree_id = df[df["tree_id"].notna()]
    # df_non_nan_tree_id.to_excel("only_matches_updated_min_angle_diff.xlsx")

    # df = pd.read_excel("real_angle_south_trees_output_meters_divide=100000_angle_divide=3_y_times=12_y_exponent=2_count_distinct_trees=256.xlsx")
    # df = pd.read_parquet('combined_data.parquet', engine="pyarrow")

    # clearance
    df.replace("None", np.nan, inplace=True)
    df["best_angle_diff"] = pd.to_numeric(df["best_angle_diff"].astype(float), errors="coerce")
    df["x_tree"] = pd.to_numeric(df["x_tree"].astype(float), errors="coerce")
    df["y_tree"] = pd.to_numeric(df["y_tree"].astype(float), errors="coerce")

    # selected_df = select_images(df=df)
    updated_df = update_df_with_min_angle_diff(df=df, is_small_survey=is_small_survey)
    # df_sorted = updated_df.sort_values(by='best_angle_diff')
    # df_subset = df.head(500)

    # Save the list of selected images to a text file
    # df_non_nan_tree_id["file_name_with_detections"].drop_duplicates().to_csv("selected_images_list.txt", index=False, header=False)

    # # Conversion factor from decimal to meters
    # conversion_factor = 100000
    # # Convert the column
    # df['distance_in_meters'] = df['distance'] * conversion_factor
    # df_sorted = df.sort_values(by='distance_in_meters')

    # df_subset = pd.read_excel(
    #     "images_rerun_0.2_0.25_meters_divide=100000_angle_divide=3_y_times=12_y_exponent=2_count_distinct_trees=1029.xlsx")

    # n = 100
    # images_list = f"images_sample_{n}.txt"
    # df_subset = get_subset_df(df=df, table_name=table_name, n=n, images_list=images_list)

    df_subset = updated_df

    # save_file_names_to_txt(df=df_subset, output_path="images_sample_100.txt")

    df_subset.loc[:, 'additional_matches'] = df_subset['additional_matches'].apply(fix_and_eval)

    df_subset['tree_name'] = df_subset['tree_name'].apply(
        lambda x: x.encode('utf-8').decode('utf-8', 'ignore') if isinstance(x, str) else x)

    return df_subset
