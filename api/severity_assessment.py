import cv2
import numpy as np

def get_severity_from_bounding_box(image_path, bounding_box):
    """
    Estimates the severity of a pothole based on its bounding box
    area relative to the total image area.

    This function is called *after* the CNN has identified a pothole
    and returned its bounding box.

    Args:
        image_path (str): The path to the user-uploaded image.
        bounding_box (tuple): A (x, y, w, h) tuple from the ML model.
                              (x, y) = top-left corner
                              (w, h) = width, height in pixels

    Returns:
        str: "Minor", "Moderate", or "Severe"
    """
    
    # 1. Load the image to get its total area
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not read image at {image_path}")
        return "Not Assessed"
    
    img_height, img_width, _ = img.shape
    total_image_area = img_height * img_width

    # 2. Get the area of the bounding box
    x, y, w, h = bounding_box
    bounding_box_area = w * h

    # 3. Calculate the percentage of the image the pothole occupies
    # We assume the user is relatively close to the pothole.
    percentage_area = (bounding_box_area / total_image_area) * 100

    # 4. Classify severity based on this percentage
    # These thresholds are adjustable and must be tuned during testing.
    
    if percentage_area < 5:
        # Pothole takes up less than 5% of the image area
        return "Minor"
    elif percentage_area < 20:
        # Pothole takes up between 5% and 20% of the image area
        return "Moderate"
    else:
        # Pothole takes up more than 20% of the image area
        return "Severe"

# --- Example of how your Flask API would use this ---
if __name__ == "__main__":
    
    # --- This data would come from your CNN Model ---
    mock_image_path = "api/26.jpg" # This needs to be a real image
    mock_cnn_bounding_box = (150, 200, 300, 200) # (x, y, w, h)
    
    # This is the function you would call from your API endpoint:
    try:
        severity = get_severity_from_bounding_box(mock_image_path, mock_cnn_bounding_box)
        print(f"Image: {mock_image_path}")
        print(f"Bounding Box: {mock_cnn_bounding_box}")
        print(f"Calculated Severity: {severity}")
    except Exception as e:
        print(f"Could not process image: {e}")
        
    print("Severity assessment script ready.")
    print("To test, update 'mock_image_path' to a real image and run.")