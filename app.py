import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import ast

# Load your Excel table into a pandas DataFrame
df = pd.read_excel("south_trees_example.xlsx")

# Loop through each row of the table
for index, row in df.iterrows():
    # Extract information from the row
    file_name = row['file_name']
    x_tree_image = row['x_tree_image']
    y_tree_image = row['y_tree_image']
    x_best_match_tree = row['x_tree']
    y_best_match_tree = row['y_tree']
    additional_matches = ast.literal_eval(row['additional_matches'])

    # Open the image
    image_path = f"images/{file_name}"  # Replace with the actual path
    image = Image.open(image_path)

    # Create a plot
    fig, ax = plt.subplots()
    ax.imshow(image)

    # Mark the current tree (red)
    ax.scatter(x_tree_image, y_tree_image, color='red', label='Current Tree', zorder=5)

    # Mark the best match tree (green)
    ax.scatter(x_best_match_tree, y_best_match_tree, color='green', label='Best Match Tree', zorder=5)

    # Mark the additional matches (blue)
    for match in additional_matches:
        print(match)
        ax.scatter(match['location_x'], match['location_y'], color='blue', label='Additional Match', zorder=5)

    # Add labels and title
    ax.set_title(f"Image: {file_name}")
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')

    # Optional: add a legend
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels)

    # Show the plot
    plt.show()
