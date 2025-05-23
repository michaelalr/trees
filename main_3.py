import ast
import math
import os
import re
from pathlib import Path
from urllib.parse import quote

import folium
import numpy as np
import pandas as pd
from folium import Element

colors_dict = {1: (230, 25, 75), 2: (60, 180, 75), 3: (255, 225, 25), 4: (0, 130, 200), 5: (245, 130, 49), 6: (145, 30, 180), 7: (70, 240, 240), 8: (240, 50, 230), 9: (210, 245, 60), 10: (250, 190, 190), 11: (0, 128, 128), 12: (230, 190, 255), 13: (170, 110, 40), 14: (255, 250, 200), 15: (128, 0, 0), 16: (170, 255, 195)}

# Add legend as an HTML element
legend_html = """
<div style="
position: fixed;
bottom: 50px;
left: 50px;
width: 200px;
background-color: white;
z-index:9999;
font-size:14px;
padding: 10px;
border: 2px solid grey;
border-radius: 8px;
box-shadow: 3px 3px 5px rgba(0,0,0,0.5);
">
<b>Legend</b><br>
<i class="fa fa-map-marker fa-2x" style="color:orange"></i> Car location<br>
<i class="fa fa-map-marker fa-2x" style="color:red"></i> Detection location<br>
<i class="fa fa-map-marker fa-2x" style="color:green"></i> Seker best match<br>
<i class="fa fa-map-marker fa-2x" style="color:blue"></i> Seker additional match<br>
</div>
"""


def create_html_with_images_and_details(df, detected_images_folder, output_html_file):
    """
    Generate an HTML file displaying image details and maps for each file_name in the dataframe.

    Args:
        df (pd.DataFrame): DataFrame containing the necessary details.
        detected_images_folder (str): Path to the folder containing detected images.
        output_html_file (str): Path to save the generated HTML file.
    """
    # Start the HTML file content
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Detections and Matches</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
            }
            .file-section {
                margin-bottom: 50px;
                border-bottom: 2px solid #ddd;
                padding-bottom: 20px;
            }
            .file-title {
                font-size: 24px;
                font-weight: bold;
                margin: 20px 0;
            }
            .row {
                display: flex;
                margin-bottom: 20px;
            }
            .left {
                flex: 50%;
                padding: 10px;
            }
            .right {
                flex: 50%;
                padding: 10px;
            }
            img {
                max-width: 100%;
                height: auto;
                border: 1px solid #ddd;
                margin-bottom: 10px;
            }
            .details {
                margin-top: 10px;
            }
            .legend {
                margin-bottom: 10px;
                padding: 5px;
                border: 1px solid #ccc;
                display: inline-block;
            }
        </style>
        
        <!-- Load Leaflet FIRST -->
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        
        <!-- Leaflet Awesome Markers (fix L undefined issue) -->
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.awesome-markers/2.0.4/leaflet.awesome-markers.css">
        <script defer src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.awesome-markers/2.0.4/leaflet.awesome-markers.min.js"></script>
        
        <!-- jQuery and Bootstrap (deferred for performance) -->
        <script defer src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
        <script defer src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

        <script>
            document.addEventListener("DOMContentLoaded", function () {
                let currentIndex = 0;
                const fileSections = document.querySelectorAll(".file-section");
                const totalCases = fileSections.length;
                const progressBar = document.getElementById("progressBar");
                const progressText = document.getElementById("progress");
                const prevBtn = document.getElementById("prevBtn");
                const nextBtn = document.getElementById("nextBtn");
    
                function showCase(index) {
                    fileSections.forEach((section, i) => {
                        section.style.display = i === index ? "block" : "none";
                    });
    
                    progressText.innerText = `Case ${index + 1} of ${totalCases}`;
                    prevBtn.disabled = index === 0;
                    nextBtn.disabled = index === totalCases - 1;
    
                    updateProgress(index, totalCases);
                }
    
                function nextCase() {
                    if (currentIndex < totalCases - 1) {
                        currentIndex++;
                        showCase(currentIndex);
                    }
                }
    
                function prevCase() {
                    if (currentIndex > 0) {
                        currentIndex--;
                        showCase(currentIndex);
                    }
                }
    
                function updateProgress(currentIndex, totalImages) {
                    let progress = ((currentIndex + 1) / totalImages) * 100;
                    progressBar.value = progress;
                }
    
                prevBtn.addEventListener("click", prevCase);
                nextBtn.addEventListener("click", nextCase);
    
                showCase(currentIndex);
            });
        </script>
    </head>
    <body>
        <h1>Detections and Matches</h1>
        <div style="text-align: center; margin-bottom: 20px;">
            <span id="progress">Case 1 of X</span><br>
            <progress id="progressBar" value="0" max="100" style="width: 100%;"></progress><br>
            <button id="prevBtn" disabled>Previous</button>
            <button id="nextBtn">Next</button>
        </div>
    """
    # Process each file_name
    for file_name in df['file_name'].unique():
        # Filter rows for the current file_name
        filtered_df = df[df['file_name'] == file_name]

        # Check if all values in the "possible_trees" column are 0
        if filtered_df['possible_trees'].eq(0).all() or filtered_df["possible_trees"].astype(np.int64).eq(0).all():
            continue  # Skip to the next file_name

        # Skip if all tree_id values are NaN
        if filtered_df['tree_id'].isna().all():
            continue

        # Get the corresponding image path
        file_name_with_detections_full_path = filtered_df.iloc[0]['file_name_with_detections']
        file_name_with_detections = Path(file_name_with_detections_full_path).name
        image_path = Path(detected_images_folder) / file_name_with_detections
        image_path_str = quote(image_path.as_posix())  # Convert path to URL format

        # Extract the number of detections from the filename (first number before "_")
        num_detections = int(file_name_with_detections.split("_")[0]) if file_name_with_detections.split("_")[0].isdigit() else 0

        # Add a section for the current file_name
        html_content += f"<div class='file-section' style='display: none;'>"

        # Add the legend section with colors corresponding to detections
        html_content += "<div class='legend'>"
        html_content += "<strong>Legend:</strong><br>"

        for i in range(1, num_detections + 1):  # Loop through the required number of colors
            color_index = (i - 1) % 16 + 1  # Cycle through colors 1 to 16
            r, g, b = colors_dict[color_index]
            html_content += f"<span style='display: inline-block; width: 20px; height: 20px; background-color: rgb({r},{g},{b}); margin-right: 5px;'></span> Tree index {i}<br>"

        html_content += "</div>"  # Close legend div

        html_content += f"<div class='file-title'>File: {file_name}</div>"

        # Add a row for image and map
        html_content += "<div class='row'>"
        html_content += "<div class='left'>"

        # Add the detected image
        html_content += f"<img src='{image_path_str}' loading='lazy' alt='Detected Image'><div class='details'>"

        det_trees_without_match = []

        # Add detection details
        for _, row in filtered_df.iterrows():
            if pd.isna(row['tree_id']):
                det_trees_without_match.append(
                    (row['tree_index'], row['real_angle'], row['x_tree_image'], row['y_tree_image']))
                continue

            html_content += "<p>"
            html_content += f"<strong>Detection Tree With Match:</strong><br>"
            html_content += f"Tree Index: {row['tree_index']}<br>"
            html_content += f"Location: ({row['x_tree_image']}, {row['y_tree_image']})<br>"
            # html_content += f"Distance (m): {row['distance_in_meters']:.3f}<br>"
            html_content += f"Real Angle (rad): {row['real_angle']:.5f}<br>"
            html_content += f"Angle Difference (deg): {row['best_angle_diff']:.5f}<br>"
            html_content += f"<strong>Best Match (Seker):</strong><br>"
            html_content += f"Tree ID: {row['tree_id']}<br>"
            html_content += f"Tree Name: {row['tree_name']}<br>"
            html_content += f"Location: ({row['x_tree']}, {row['y_tree']})<br>"
            html_content += "</p>"

        if len(det_trees_without_match) > 0:
            html_content += f"<strong>Detection Trees Without Match</strong>"
            for tree in det_trees_without_match:
                tree_index, real_angle, x_tree_image, y_tree_image = tree
                html_content += "<p>"
                html_content += f"Tree Index: {tree_index}<br>"
                html_content += f"Real Angle (rad): {real_angle:.5f}<br>"
                html_content += f"Location: ({x_tree_image}, {y_tree_image})<br>"
                html_content += "</p>"

        # Additional matches
        # Replace 'nan' with 'None' in the 'additional_matches' column
        # Convert the 'additional_matches' string to a list of dictionaries
        filtered_df.loc[:, 'additional_matches'] = filtered_df['additional_matches'].apply(
            lambda x: ast.literal_eval(x.replace('nan', 'None')) if isinstance(x, str) else x
        )

        # if not pd.isna(filtered_df.iloc[0]['additional_matches']):
        # if len(filtered_df.iloc[0]['additional_matches']) > 0:
        additional_matches = filtered_df.iloc[0]['additional_matches']
        if additional_matches:
            html_content += f"<strong>Seker Matches:</strong>"
            for match in filtered_df.iloc[0]['additional_matches']:
                html_content += "<p>"
                html_content += f"ID: {match['id']}<br>"
                html_content += f"Tree Name: {match['tree_name']}<br>"
                html_content += f"Location: ({match['location_x']}, {match['location_y']})<br>"
                html_content += "</p>"

        html_content += "</div></div>"

        # Generate the map
        html_content += "<div class='right'>"
        map_path = generate_map(filtered_df)
        html_content += f"<iframe src='{map_path}' width='100%' height='500px'></iframe>"
        html_content += "</div></div>"

        html_content += "</div>"  # Close file-section

    # End the HTML content
    html_content += """
    </body>
    </html>
    """

    # Save the HTML content to a file
    with open(output_html_file, 'w', encoding='utf-8') as file:
        file.write(html_content)


def generate_map(filtered_df):
    """
    Generate a map for the given file_name using filtered DataFrame rows.

    Args:
        filtered_df (pd.DataFrame): Filtered rows for a specific file_name.

    Returns:
        str: Path to the saved map HTML file.
    """
    # Create a map centered on the first detection
    initial_coords = [filtered_df.iloc[0]['y_tree_image'], filtered_df.iloc[0]['x_tree_image']]
    map_obj = folium.Map(location=initial_coords, zoom_start=15)
    # Line length (adjust for visibility)
    line_length = 0.0001  # Approx ~10 meters
    best_match_ids = filtered_df['tree_id'].unique()

    # Add markers for best matches, detections directions and additional matches
    for _, row in filtered_df.iterrows():
        # Best match not nan
        if pd.notna(row['tree_id']):
            folium.Marker(
                location=[row['y_tree'], row['x_tree']],
                popup=f"Best Match: {row['tree_name']} (ID: {row['tree_id']})",
                icon=folium.Icon(color='green')
            ).add_to(map_obj)
            # Detection location
            # Compute endpoint using trigonometry
            x_end = row['x_tree'] + line_length * math.cos(row['real_angle'])
            y_end = row['y_tree'] + line_length * math.sin(row['real_angle'])
            # Add a line representing detection direction
            folium.PolyLine(
                locations=[(row['y_tree'], row['x_tree']), (y_end, x_end)],
                popup=f"Detection: Tree Index {row['tree_index']}, angle: {row['real_angle']}",
                color="black",
                weight=2
            ).add_to(map_obj)
            # # Draw a line between the detection tree and the matched seker tree
            # folium.PolyLine(
            #     locations=[[row['y_tree_image'], row['x_tree_image']], [row['y_tree'], row['x_tree']]],
            #     color='black',  # Color for the connection line
            #     weight=2  # Line thickness
            # ).add_to(map_obj)

        # Additional matches
        # if pd.notna(row['additional_matches']):
        # if len(row['additional_matches']) > 0:
        if row['additional_matches']:
            for match in row['additional_matches']:
                id = match['id']
                if id not in best_match_ids:
                    folium.Marker(
                        location=[match['location_y'], match['location_x']],
                        popup=f"Additional Match: {match['tree_name']} (ID: {match['id']})",
                        icon=folium.Icon(color='blue')
                    ).add_to(map_obj)

        # Detection location
        # # Create Google Street View URL for the current tree
        # x_tree_image = row['x_tree_image']
        # y_tree_image = row['y_tree_image']
        # current_tree_streetview_url = f"https://www.google.com/maps?q={y_tree_image},{x_tree_image}&layer=c&cbll={y_tree_image},{x_tree_image}"
        # folium.Marker(
        #     location=[y_tree_image, x_tree_image],
        #     popup=f"Detection: Tree Index {row['tree_index']}<br><a href='{current_tree_streetview_url}' target='_blank'>View on Google Street View</a>",
        #     icon=folium.Icon(color='red')
        # ).add_to(map_obj)

        # Car location
        x_car = row['x_image']
        y_car = row['y_image']
        heading = row['heading']
        current_tree_streetview_url = f"https://www.google.com/maps?q={y_car},{x_car}&layer=c&cbll={y_car},{x_car}&cbp=12,{heading},0,0,0"
        folium.Marker(
            location=[y_car, x_car],
            popup=f"Car location<br><a href='{current_tree_streetview_url}' target='_blank'>View on Google Street View</a>",
            icon=folium.Icon(color='orange')
        ).add_to(map_obj)

    map_obj.get_root().html.add_child(Element(legend_html))

    # Save the map to an HTML file
    map_path = f"./maps/map_{filtered_df.iloc[0]['file_name']}.html"
    os.makedirs(os.path.dirname(map_path), exist_ok=True)
    map_obj.save(map_path)

    return map_path


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


def update_df_with_min_angle_diff(df, min_threshold=20, second_threshold=30):
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

if __name__ == '__main__':
    table_name = "nadav_output_meters_divide=100000_angle_divide=3_y_times=12_y_exponent=2_count_distinct_trees=608.xlsx"
    df = pd.read_excel(table_name)
    # df = pd.read_excel("all_trees_updated_min_angle_diff.xlsx")
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
    updated_df = update_df_with_min_angle_diff(df=df)
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



    detected_images_folder = "detected_images/tree_nadav_merged"
    output_html_file = "index.html"
    create_html_with_images_and_details(df=df_subset, detected_images_folder=detected_images_folder,
                                        output_html_file=output_html_file)
