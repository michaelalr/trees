import os
import zipfile

import pandas as pd


def extract_images_from_zip(csv_path, zip_path, image_column, output_dir):
    # 1. Load target filenames from CSV (basename only)
    df = pd.read_csv(csv_path)
    target_filenames = set(os.path.basename(f) for f in df[image_column])

    # 2. Open the zip file
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Get list of all files in the zip
        zip_files = zip_ref.namelist()

        # Create output dir if not exists
        os.makedirs(output_dir, exist_ok=True)

        # Track which ones were found
        found_files = set()

        for zip_file in zip_files:
            name_in_zip = os.path.basename(zip_file)
            if name_in_zip in target_filenames:
                # Extract this file
                zip_ref.extract(zip_file, output_dir)
                found_files.add(name_in_zip)

        # Find which ones were missing
        missing_files = target_filenames - found_files
        if missing_files:
            print("\nMissing files:")
            for fname in sorted(missing_files):
                print(f"❌ {fname}")
        else:
            print("\n✅ All files were found and extracted.")


if __name__ == '__main__':
    csv_path = "images_list_for_nadav.csv"
    zip_path = "ALL_GSV.zip"
    image_column = "filename"
    output_dir = "images_to_download"
    extract_images_from_zip(csv_path=csv_path, zip_path=zip_path, image_column=image_column, output_dir=output_dir)
