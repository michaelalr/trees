import ast
import os
from pathlib import Path

import folium
import pandas as pd
from folium import Element

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
        </style>
    </head>
    <body>
    <h1>Detections and Matches</h1>
    """
    # Process each file_name
    for file_name in df['file_name'].unique():
        # Filter rows for the current file_name
        filtered_df = df[df['file_name'] == file_name]

        # Check if all values in the "possible_trees" column are 0
        if filtered_df['possible_trees'].eq(0).all():
            continue  # Skip to the next file_name

        # Get the corresponding image path
        file_name_with_detections_full_path = filtered_df.iloc[0]['file_name_with_detections']
        file_name_with_detections = Path(file_name_with_detections_full_path).name
        image_path = os.path.join(detected_images_folder, file_name_with_detections)

        # Add a section for the current file_name
        html_content += f"<div class='file-section'>"
        html_content += f"<div class='file-title'>File: {file_name}</div>"

        # Add a row for image and map
        html_content += "<div class='row'>"
        html_content += "<div class='left'>"

        # Add the detected image
        html_content += f"<img src='{image_path}' alt='Detected Image'><div class='details'>"

        det_trees_without_match = []

        # Add detection details
        for _, row in filtered_df.iterrows():
            if pd.isna(row['tree_id']):
                det_trees_without_match.append((row['tree_index'], row['x_tree_image'], row['y_tree_image']))
                continue

            html_content += "<p>"
            html_content += f"<strong>Detection Tree With Match:</strong><br>"
            html_content += f"Tree Index: {row['tree_index']}<br>"
            html_content += f"Location: ({row['x_tree_image']}, {row['y_tree_image']})<br>"
            html_content += f"Distance (m): {row['distance_in_meters']:.3f}<br>"
            html_content += f"<strong>Best Match (Seker):</strong><br>"
            html_content += f"Tree ID: {row['tree_id']}<br>"
            html_content += f"Tree Name: {row['tree_name']}<br>"
            html_content += f"Location: ({row['x_tree']}, {row['y_tree']})<br>"
            html_content += "</p>"

        if len(det_trees_without_match) > 0:
            html_content += f"<strong>Detection Trees Without Match</strong>"
        for tree in det_trees_without_match:
            tree_index, x_tree_image, y_tree_image = tree
            html_content += "<p>"
            html_content += f"Tree Index: {tree_index}<br>"
            html_content += f"Location: ({x_tree_image}, {y_tree_image})<br>"
            html_content += "</p>"

        # Additional matches
        # Replace 'nan' with 'None' in the 'additional_matches' column
        # Convert the 'additional_matches' string to a list of dictionaries
        filtered_df.loc[:, 'additional_matches'] = filtered_df['additional_matches'].apply(
            lambda x: ast.literal_eval(x.replace('nan', 'None')) if isinstance(x, str) else x
        )

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

    best_match_ids = filtered_df['tree_id'].unique()

    # Add markers for best matches and additional matches
    for _, row in filtered_df.iterrows():
        # Best match not nan
        if pd.notna(row['tree_id']):
            folium.Marker(
                location=[row['y_tree'], row['x_tree']],
                popup=f"Best Match: {row['tree_name']} (ID: {row['tree_id']})",
                icon=folium.Icon(color='green')
            ).add_to(map_obj)
            # Draw a line between the detection tree and the matched seker tree
            folium.PolyLine(
                locations=[[row['y_tree_image'], row['x_tree_image']], [row['y_tree'], row['x_tree']]],
                color='black',  # Color for the connection line
                weight=2  # Line thickness
            ).add_to(map_obj)

        # Additional matches
        for match in row['additional_matches']:
            id = match['id']
            if id not in best_match_ids:
                folium.Marker(
                    location=[match['location_y'], match['location_x']],
                    popup=f"Additional Match: {match['tree_name']} (ID: {match['id']})",
                    icon=folium.Icon(color='blue')
                ).add_to(map_obj)

        # Detection location
        # Create Google Street View URL for the current tree
        x_tree_image = row['x_tree_image']
        y_tree_image = row['y_tree_image']
        current_tree_streetview_url = f"https://www.google.com/maps?q={y_tree_image},{x_tree_image}&layer=c&cbll={y_tree_image},{x_tree_image}"
        folium.Marker(
            location=[y_tree_image, x_tree_image],
            popup=f"Detection: Tree Index {row['tree_index']}<br><a href='{current_tree_streetview_url}' target='_blank'>View on Google Street View</a>",
            icon=folium.Icon(color='red')
        ).add_to(map_obj)

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


if __name__ == '__main__':
    df = pd.read_excel("south_trees_output_meters_divide=100000_angle_divide=3_y_times=12_y_exponent=2_count_distinct_trees=256.xlsx")

    # Conversion factor from decimal to meters
    conversion_factor = 100000
    # Convert the column
    df['distance_in_meters'] = df['distance'] * conversion_factor
    df_sorted = df.sort_values(by='distance_in_meters')

    df_sorted['tree_name'] = df_sorted['tree_name'].apply(
        lambda x: x.encode('utf-8').decode('utf-8', 'ignore') if isinstance(x, str) else x)

    detected_images_folder = "detected_images"
    output_html_file = "index.html"
    create_html_with_images_and_details(df=df_sorted, detected_images_folder=detected_images_folder,
                                        output_html_file=output_html_file)
