import kagglehub
import os
import shutil

print("Downloading pothole dataset from Kaggle...")

# Download dataset
path = kagglehub.dataset_download("atulyakumar98/pothole-detection-dataset")

print(f"Dataset downloaded to: {path}")

# Copy to your project structure
project_data_path = "data/raw/pothole_dataset"

# Create directory if it doesn't exist
os.makedirs("data/raw", exist_ok=True)

if not os.path.exists(project_data_path):
    print(f"Copying to {project_data_path}...")
    shutil.copytree(path, project_data_path)
    print("Copy complete!")
else:
    print(f"Dataset already exists at {project_data_path}")

# Show what's in the dataset
print("\nDataset contents:")
for root, dirs, files in os.walk(project_data_path):
    level = root.replace(project_data_path, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 2 * (level + 1)
    for file in files[:5]:  # Show first 5 files only
        print(f"{subindent}{file}")
    if len(files) > 5:
        print(f"{subindent}... and {len(files) - 5} more files")