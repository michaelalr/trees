import pandas as pd
import folium
import ast

# Load your Excel table into a pandas DataFrame
df = pd.read_excel("south_trees_example_2.xlsx")

# Define the initial map center (e.g., the middle of the coordinates you're working with)
map_center_lat = 32.03127788  # Set the central latitude for your map
map_center_lon = 34.75298463  # Set the central longitude for your map
zoom_start = 18  # Set the initial zoom level (higher = more zoomed in)

# Create a map centered at the specified location
m = folium.Map(location=[map_center_lat, map_center_lon], zoom_start=zoom_start)

# Loop through each row of the table
for index, row in df.iterrows():
    # Extract tree information from the row
    file_name = row['file_name']
    x_tree_image = row['x_tree_image']
    y_tree_image = row['y_tree_image']
    x_best_match_tree = row['x_tree']
    y_best_match_tree = row['y_tree']

    # Convert the 'additional_matches' string to a list of dictionaries
    additional_matches = ast.literal_eval(row['additional_matches'])

    # Create Google Street View URL for the current tree
    current_tree_streetview_url = f"https://www.google.com/maps?q={y_tree_image},{x_tree_image}&layer=c&cbll={y_tree_image},{x_tree_image}"

    # Add an offset for visibility (for example, a small random value to separate them slightly)
    offset = 0.00000005  # Small offset to make sure markers are not on top of each other

    # Add the current tree location to the map (red)
    # folium.Marker([y_tree_image, x_tree_image], popup=f"Current Tree: {row['tree_index']} - {file_name}",
    #               icon=folium.Icon(color='blue')).add_to(m)
    # Add the current tree location to the map (red)
    folium.Marker([y_tree_image, x_tree_image],
                  popup=f"Current Tree: {file_name}<br><a href='{current_tree_streetview_url}' target='_blank'>View on Google Street View</a>",
                  icon=folium.Icon(color='red', icon='cloud', icon_color='white')).add_to(m)


    # Add the best match tree location to the map (green)
    # folium.Marker([y_best_match_tree, x_best_match_tree], popup=f"Best Match Tree: {row['tree_id']} {file_name}",
    #               icon=folium.Icon(color='green')).add_to(m)
    # folium.Marker([y_best_match_tree + offset*2, x_best_match_tree + offset*2], popup=f"Best Match Tree: {row['tree_id']} {file_name}",
    #               icon=folium.Icon(color='green')).add_to(m)
    # Create Google Street View URL for the best match tree
    best_match_tree_streetview_url = f"https://www.google.com/maps?q={y_best_match_tree},{x_best_match_tree}&layer=c&cbll={y_best_match_tree},{x_best_match_tree}"
    # Add the best match tree location to the map (green)
    folium.Marker([y_best_match_tree, x_best_match_tree],
                  popup=f"Best Match Tree: {file_name}<br><a href='{best_match_tree_streetview_url}' target='_blank'>View on Google Street View</a>",
                  icon=folium.Icon(color='green', icon='cloud', icon_color='white')).add_to(m)


    # Add the additional matches to the map (blue)
    # for match in additional_matches:
    #     match_x = match['location_x']
    #     match_y = match['location_y']
    #     # folium.Marker([match_y, match_x], popup=f"Additional Match: {match['id']} {match['tree_name']}",
    #     #               icon=folium.Icon(color='red')).add_to(m)
    #     additional_match_streetview_url = f"https://www.google.com/maps?q={match_y},{match_x}&layer=c&cbll={match_y},{match_x}"
    #     folium.Marker([match_y, match_x],
    #                   popup=f"Additional Match: {match['tree_name']}<br><a href='{additional_match_streetview_url}' target='_blank'>View on Google Street View</a>",
    #                   icon=folium.Icon(color='blue', icon='cloud', icon_color='white')).add_to(m)


# Save the map to an HTML file
m.save("tree_locations_map.html")
