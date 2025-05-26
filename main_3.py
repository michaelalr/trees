import ast
import math
import os
from pathlib import Path
from urllib.parse import quote

import folium
import pandas as pd
from folium import Element

from clean_data_before_json import clean_df

colors_dict = {1: (230, 25, 75), 2: (60, 180, 75), 3: (255, 225, 25), 4: (0, 130, 200), 5: (245, 130, 49),
               6: (145, 30, 180), 7: (70, 240, 240), 8: (240, 50, 230), 9: (210, 245, 60), 10: (250, 190, 190),
               11: (0, 128, 128), 12: (230, 190, 255), 13: (170, 110, 40), 14: (255, 250, 200), 15: (128, 0, 0),
               16: (170, 255, 195)}

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


def render_case_column(filtered_df, detected_images_folder, left_or_right=""):
    """
    Given a filtered_df for one file_name, produce the HTML
    for: map iframe, image-with-detections, and details.
    """
    html = []

    # 1) Map (half-width wrapper is handled by parent .left/.right)
    map_path = generate_map(filtered_df, left_or_right)
    html.append(
        "<div style='margin-bottom:20px;'>"
        f"<iframe src='{map_path}' width='100%' height='500px'></iframe>"
        "</div>"
    )

    # 2) Detected image
    full_path = filtered_df.iloc[0]['file_name_with_detections']
    fname = Path(full_path).name
    img_url = quote((Path(detected_images_folder) / fname).as_posix())
    html.append(f"<img src='{img_url}' loading='lazy' alt='Detected Image'>")

    # 3) Details
    html.append("<div class='details'>")
    # — matched trees
    for _, row in filtered_df.iterrows():
        if pd.isna(row['tree_id']):
            continue
        html.append(
            "<p>"
            "<strong>Detection Tree With Match:</strong><br>"
            f"Tree Index: {row['tree_index']}<br>"
            f"Location: ({row['x_tree_image']}, {row['y_tree_image']})<br>"
            f"Real Angle (rad): {row['real_angle']:.5f}<br>"
            f"Angle Difference (deg): {row['best_angle_diff']:.5f}<br>"
            "<strong>Best Match (Seker):</strong><br>"
            f"Tree ID: {int(row['tree_id'])}<br>"
            f"Tree Name: {row['tree_name']}<br>"
            f"Location: ({row['x_tree']}, {row['y_tree']})<br>"
            "</p>"
        )
    # — unmatched detections
    unmatched = [
        (r['tree_index'], r['real_angle'], r['x_tree_image'], r['y_tree_image'])
        for _, r in filtered_df.iterrows() if pd.isna(r['tree_id'])
    ]
    if unmatched:
        html.append("<strong>Detection Trees Without Match</strong>")
        for idx, ang, x_img, y_img in unmatched:
            html.append(
                "<p>"
                f"Tree Index: {idx}<br>"
                f"Real Angle (rad): {ang:.5f}<br>"
                f"Location: ({x_img}, {y_img})<br>"
                "</p>"
            )
    # additional Seker matches
    # ensure it's a real list, not a string
    filtered_df.loc[:, 'additional_matches'] = filtered_df['additional_matches'].apply(
        lambda x: ast.literal_eval(x.replace('nan', 'None')) if isinstance(x, str) else x
    )
    extras = filtered_df.iloc[0]['additional_matches']
    if extras:
        html.append("<strong>Potential Seker Trees:</strong>")
        valid_ids = set(
            filtered_df['tree_id']
            .dropna()  # remove NaNs
            .astype(int)  # cast to ints
            .tolist()  # make a Python list
        )
        for m in extras:
            if m['id'] not in valid_ids:
                html.append(
                    "<p>"
                    f"ID: {m['id']}<br>"
                    f"Tree Name: {m['tree_name']}<br>"
                    f"Location: ({m['location_x']}, {m['location_y']})<br>"
                    "</p>"
                )

    html.append("</div>")  # close .details

    return "\n".join(html)


def create_html_with_images_and_details(df_tlv_survey, detected_images_folder, output_html_file,
                                        df_small_survey=pd.DataFrame()):
    """
    Generate an HTML file displaying image details and maps for each file_name in the dataframe.

    Args:
        df_tlv_survey (pd.DataFrame): DataFrame containing the necessary details.
        detected_images_folder (str): Path to the folder containing detected images.
        output_html_file (str): Path to save the generated HTML file.
        df_small_survey (pd.DataFrame)
    """
    # Start the HTML file content
    html = """
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
    unique_files = df_tlv_survey['file_name'].unique()[:200]

    for file_name in unique_files:
        # Filter rows for the current file_name
        tlv = df_tlv_survey[df_tlv_survey['file_name'] == file_name]
        if df_small_survey.empty:
            # Skip if no detections or no matches in either
            if (tlv['possible_trees'].astype(int).eq(0).all() or tlv['tree_id'].isna().all()):
                continue
        else:
            small = df_small_survey[df_small_survey['file_name'] == file_name]

            # Skip if no detections or no matches in either
            if ((tlv['possible_trees'].astype(int).eq(0).all() and small['possible_trees'].astype(int).eq(0).all())
                    or (tlv['tree_id'].isna().all() and small['tree_id'].isna().all())):
                continue

        # File title + legend (shared)
        html += "<div class='file-section' style='display:none;'>"
        html += f"<div class='file-title'>File: {file_name}</div>"

        # Legend
        fname = Path(tlv.iloc[0]['file_name_with_detections']).name
        num_det = int(fname.split("_")[0]) if fname.split("_")[0].isdigit() else 0
        html += "<div class='legend'><strong>Legend:</strong><br>"
        for i in range(1, num_det + 1):
            idx = (i - 1) % 16 + 1
            r, g, b = colors_dict[idx]
            html += (
                f"<span style='display:inline-block;width:20px;height:20px;"
                f"background-color:rgb({r},{g},{b});margin-right:5px;'></span>"
                f"Tree index {i}<br>"
            )
        html += "</div>"

        # Two-column: TLV on left, small on right
        html += "<div class='row'>"

        html += "<div class='left'>"
        html += "<h3>TLV Survey</h3>"
        html += render_case_column(tlv, detected_images_folder, "left")
        html += "</div>"

        if not df_small_survey.empty:
            html += "<div class='right'>"
            html += "<h3>Small Survey</h3>"
            html += render_case_column(small, detected_images_folder, "right")
            html += "</div>"

        html += "</div>"  # close .row

        html += "</div>"  # Close file-section

    html += "</body></html>"

    # Write out
    with open(output_html_file, 'w', encoding='utf-8') as f:
        f.write(html)


def generate_map(filtered_df, left_or_right=""):
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
    maps_repo = "maps"
    direction = "" if left_or_right == "" else f"{left_or_right}_"
    map_path = f"./{maps_repo}/{direction}map_{filtered_df.iloc[0]['file_name']}.html"
    os.makedirs(os.path.dirname(map_path), exist_ok=True)
    map_obj.save(map_path)

    return map_path


def main():
    small_survey = "tree_small_survey_output_meters_divide=100000_angle_divide=3_y_times=12_y_exponent=2_count_distinct_trees=0.xlsx"
    df_small_survey = pd.read_excel(small_survey)

    tlv_survey = "nadav_output_meters_divide=100000_angle_divide=3_y_times=12_y_exponent=2_count_distinct_trees=608.xlsx"
    df_tlv_survey = pd.read_excel(tlv_survey)

    clean_df_small_survey = clean_df(df=df_small_survey, is_small_survey=True)
    clean_df_tlv_survey = clean_df(df=df_tlv_survey, is_small_survey=False)

    detected_images_folder = "detected_images/tree_nadav_merged"
    output_html_file = "index.html"
    create_html_with_images_and_details(df_tlv_survey=clean_df_tlv_survey,
                                        detected_images_folder=detected_images_folder,
                                        output_html_file=output_html_file, df_small_survey=clean_df_small_survey)


if __name__ == '__main__':
    main()
