from bing_image_downloader import downloader
import os

# Create output directory
os.makedirs('data/raw/nigerian_scraped', exist_ok=True)

queries = [
    "Nigeria road potholes",
    "Lagos road damage", 
    "Nigerian highway potholes",
    "bad roads Nigeria",
    "Abuja road cracks",
    "Port Harcourt road conditions",
    "Nigerian road deterioration",
    "Ibadan road potholes"
]

for query in queries:
    try:
        print(f"\nDownloading: {query}")
        downloader.download(
            query=query,
            limit=30,  # 30 per query = ~240 total
            output_dir='data/raw/nigerian_scraped',
            adult_filter_off=True,
            force_replace=False,
            timeout=60,
            verbose=True
        )
    except Exception as e:
        print(f"Error with {query}: {e}")

print("\nDownload complete! Check data/raw/nigerian_scraped/")