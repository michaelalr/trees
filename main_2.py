import pandas as pd
import folium

# Load the Detection Table
detection_trees = pd.read_excel("south_trees_output_meters_divide=100000_angle_divide=3_y_times=12_y_exponent=2_count_distinct_trees=316.xlsx")
# Group by 'tree_id' and find the row with the minimum distance
# detection_trees = detection_trees.loc[detection_trees.groupby('tree_id')['distance'].idxmin()]
# Reset the index if necessary
# detection_trees = detection_trees.reset_index(drop=True)
# detection_trees.to_csv("min_distance_df.csv")

# Load the Seker Table
seker_trees = pd.read_csv("data_tree_with_wgs.csv", encoding="ISO-8859-1")

# Drop rows with NaN values in x or y for both tables
detection_trees = detection_trees.dropna(subset=['x_tree_image', 'y_tree_image'])
detection_trees = detection_trees[detection_trees["tree_id"].notna()]
seker_trees = seker_trees.dropna(subset=['x', 'y'])

# Define the map center (calculate based on the average of all coordinates)
all_latitudes = pd.concat([detection_trees['y_tree_image'], seker_trees['y']])
all_longitudes = pd.concat([detection_trees['x_tree_image'], seker_trees['x']])
map_center_lat = all_latitudes.mean()
map_center_lon = all_longitudes.mean()

# Create an interactive map
m = folium.Map(location=[map_center_lat, map_center_lon], zoom_start=14)

ids_with_match = []

# Add markers for Detection Table
for index, row in detection_trees.iterrows():
    file_name = row['file_name']
    latitude = row['y_tree_image']
    longitude = row['x_tree_image']
    tree_id = row['row_id']
    tree_name = row.get('tree_name', 'Unknown Tree')  # Use 'tree_name' if available

    # Create Google Street View URL for the current tree
    current_tree_streetview_url = f"https://www.google.com/maps?q={latitude},{longitude}&layer=c&cbll={latitude},{longitude}"

    # Find the matching tree in Table 2 (seker trees) based on tree_id and OBJECTID
    seker_id = row['tree_id']
    ids_with_match.append(seker_id)
    matched_seker_tree = seker_trees[seker_trees['OBJECTID'] == seker_id]

    if not matched_seker_tree.empty:
        # Add a marker for Detection Table
        folium.Marker(
            location=[latitude, longitude],
            popup=f"Current Tree: {file_name}<br>Tree Name: {tree_name}<br>id: {tree_id}<br><a href='{current_tree_streetview_url}' target='_blank'>View on Google Street View</a>",
            icon=folium.Icon(color='blue')
        ).add_to(m)

        matched_row = matched_seker_tree.iloc[0]
        latitude_seker = matched_row['y']
        longitude_seker = matched_row['x']
        tree_name_seker = matched_row.get('Tree_name_new', 'Unknown Tree')

        # Add an offset for visibility (for example, a small random value to separate them slightly)
        offset = 0  # Small offset to make sure markers are not on top of each other

        # Add a marker for Seker Table from red to green
        folium.Marker(
            location=[latitude_seker + offset, longitude_seker + offset],
            popup=f"Tree Name: {tree_name_seker}<br>id: {seker_id}",
            icon=folium.Icon(color='green')
        ).add_to(m)

        # Draw a line between the detection tree and the matched seker tree
        # folium.PolyLine(
        #     locations=[[latitude, longitude], [latitude_seker, longitude_seker]],
        #     color='black',  # Color for the connection line
        #     weight=2  # Line thickness
        # ).add_to(m)

    else:  # there is no match
        # Add a marker for Detection Table
        folium.Marker(
            location=[latitude, longitude],
            popup=f"Tree Name: {tree_name}<br>id: {tree_id}",
            icon=folium.Icon(color='lightblue')
        ).add_to(m)

# Add markers for Seker Table
for index, row in seker_trees.iterrows():
    latitude = row['y']
    longitude = row['x']
    seker_id = row['OBJECTID']
    tree_name = row.get('Tree_name_new', 'Unknown Tree')  # Use 'tree_name' if available

    if seker_id not in ids_with_match:
        # Add a marker for Seker Table in red
        folium.Marker(
            location=[latitude, longitude],
            popup=f"Tree Name: {tree_name}<br>id: {seker_id}",
            icon=folium.Icon(color='red')
        ).add_to(m)

# Save the map to an HTML file
m.save("trees_interactive_map.html")
