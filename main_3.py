import os
import pandas as pd
import folium
import ast
from pathlib import Path


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

        # Get the corresponding image path
        file_name_with_detections_full_path = filtered_df.iloc[0]['file_name_with_detections']
        file_name_with_detections = Path(file_name_with_detections_full_path).name
        print("detected_images_folder: ", detected_images_folder)
        print("file_name_with_detections_full_path: ", file_name_with_detections_full_path)
        print("file_name_with_detections: ", file_name_with_detections)
        image_path = os.path.join(detected_images_folder, file_name_with_detections)

        # Add a section for the current file_name
        html_content += f"<div class='file-section'>"
        html_content += f"<div class='file-title'>File: {file_name}</div>"

        # Add a row for image and map
        html_content += "<div class='row'>"
        html_content += "<div class='left'>"

        # Add the detected image
        print("image_path:", image_path)
        html_content += f"<img src='{image_path}' alt='Detected Image'><div class='details'>"

        # Add detection details
        for _, row in filtered_df.iterrows():
            html_content += "<p>"
            html_content += f"<strong>Detection Details:</strong><br>"
            html_content += f"Tree Index: {row['tree_index']}<br>"
            html_content += f"Location: ({row['x_tree_image']}, {row['y_tree_image']})<br>"
            html_content += f"Distance: {row['distance']}<br>"
            html_content += f"<strong>Seker Details - Best Match:</strong><br>"
            html_content += f"Tree ID: {row['tree_id']}<br>"
            html_content += f"Tree Name: {row['tree_name']}<br>"
            html_content += f"Location: ({row['x_tree']}, {row['y_tree']})<br>"

            # Additional matches
            html_content += f"<strong>Seker Details - Additional Matches:</strong><br>"
            # Convert the 'additional_matches' string to a list of dictionaries
            additional_matches = ast.literal_eval(row['additional_matches'])
            for match in additional_matches:
                print(match)
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
    with open(output_html_file, 'w') as file:
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
    initial_coords = [filtered_df.iloc[0]['y_tree'], filtered_df.iloc[0]['x_tree']]
    map_obj = folium.Map(location=initial_coords, zoom_start=15)

    # Add markers for best matches and additional matches
    for _, row in filtered_df.iterrows():
        # Best match
        folium.Marker(
            location=[row['y_tree'], row['x_tree']],
            popup=f"Best Match: {row['tree_name']} (ID: {row['tree_id']})",
            icon=folium.Icon(color='green')
        ).add_to(map_obj)

        # Additional matches
        # Convert the 'additional_matches' string to a list of dictionaries
        additional_matches = ast.literal_eval(row['additional_matches'])
        for match in additional_matches:
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

    # Save the map to an HTML file
    map_path = f"./maps/map_{filtered_df.iloc[0]['file_name']}.html"
    os.makedirs(os.path.dirname(map_path), exist_ok=True)
    map_obj.save(map_path)

    return map_path


if __name__ == '__main__':
    df = pd.read_excel("south_trees_example_3.xlsx")
    detected_images_folder = "detected_images"
    output_html_file = "index.html"
    create_html_with_images_and_details(df=df, detected_images_folder=detected_images_folder,
                                        output_html_file=output_html_file)
