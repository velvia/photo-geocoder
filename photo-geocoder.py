#
# Description: This script reads the EXIF geolocation data from images in a folder (including .heic and .jpg),
#     reverse geocodes, looks up city/suburb/town name from the coords, and renames images with the location name
#     as a suffix.
# It is fairly slow because it uses the Nominatim API for reverse geocoding. The script also caches the results.
#
# Usage: python photo-geocoder.py <folder_path>
#
# Note that it tries to be specific, using suburb, district, town, and city in that order.  In many cases
# suburb or town information is available but not city, so this way this script can get more hits.
#
# I developed this quickly with the help of ChatGPT and some personal debugging, direction, and enhancements.
# I have not tested this script extensively, so please use it with caution and test it on a small dataset first.
#
import os
import subprocess
import sys
import requests
import geopy.exc
from PIL import Image
from PIL.ExifTags import TAGS
from time import sleep
import json
from geopy.geocoders import Nominatim

# Geocoding cache
geocode_cache = {}

# Helper function to round lat, lon to N decimal places
def round_coords(lat, lon, decimals=4):
    factor = 10 ** decimals
    return round(lat * factor) / factor, round(lon * factor) / factor

# Caching mechanism with rounded coordinates
class GeocodeCache:
    def __init__(self, tolerance=0.025, decimals=4):
        self.cache = {}
        self.tolerance = tolerance  # This can be used for controlling rounding precision
        self.decimals = decimals  # Precision of rounding (default 4 decimal places)

    def get_cached_location(self, lat, lon):
        # Round the coordinates to the specified decimal places
        rounded_lat, rounded_lon = round_coords(lat, lon, self.decimals)

        # Check if the rounded coordinates are already cached
        return self.cache.get((rounded_lat, rounded_lon), None)

    def cache_location(self, lat, lon, location):
        # Round the coordinates to the specified decimal places
        rounded_lat, rounded_lon = round_coords(lat, lon, self.decimals)

        # Store the location in the cache using the rounded coordinates as the key
        self.cache[(rounded_lat, rounded_lon)] = location


def get_lat_lon_from_exif(image_path):
    """Extracts latitude and longitude from EXIF data using exiftool."""
    try:
        result = subprocess.run(
            ['exiftool', '-n', '-GPSLatitude', '-GPSLongitude', image_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        # Parse the output directly into latitude and longitude (decimal degrees)
        lines = result.stdout.splitlines()
        lat = None
        lon = None

        for line in lines:
            if 'GPS Latitude' in line:  # Handle the space between 'GPS' and 'Latitude'
                lat = float(line.split(":")[1].strip())
            elif 'GPS Longitude' in line:  # Handle the space between 'GPS' and 'Longitude'
                lon = float(line.split(":")[1].strip())

        if lat is not None and lon is not None:
            return lat, lon
        else:
            print(f"No GPS data found in {image_path}")
            return None
    except Exception as e:
        print(f"Error extracting EXIF from {image_path}: {e}")
        return None

def convert_to_decimal(degrees, ref):
    """Converts GPS coordinates from DMS to decimal degrees."""
    decimal = 0.0
    for i, d in enumerate(degrees):
        decimal += float(d) / (60 ** i)

    if ref in ['S', 'W']:
        decimal = -decimal

    return decimal


# Geocode function with caching and rounding coordinates
def geocode(lat, lon, cache):
    """Reverse geocodes the given latitude and longitude, suburb, district, town, city (in that order)."""
    # Check if this location is in the cache using rounded coordinates
    location = cache.get_cached_location(lat, lon)

    if location:
        print(f"Using cached location: {location}")
        return location
    try:
        # Initialize Nominatim geolocator
        geolocator = Nominatim(user_agent="YourAppName/1.0 (your@email.com)")

        # Geocode the coordinates (lat, lon)
        location = geolocator.reverse((lat, lon), language='en', exactly_one=True)

        # Check if location is found and return the city
        if location:
            address = location.raw.get("address", {})
            location = address.get("suburb", address.get("district", address.get("town", address.get("city", ""))))
            if location:
                cache.cache_location(lat, lon, location)
                return location
            else:
                print(f"\tNo city/suburb/town found for coordinates: {lat}, {lon}")
                return None
        else:
            print(f"\tERR: Unable to find location for coordinates: {lat}, {lon}")
            return None
    except Exception as e:
        print(f"Error in geocoding: {e}")
        return None


def rename_image(image_path, city_name):
    """Renames image file to append city name."""
    if not city_name:
        return

    dir_name, file_name = os.path.split(image_path)
    base_name, ext = os.path.splitext(file_name)

    new_name = f"{base_name}-{city_name.replace(' ', '')}{ext}"
    new_path = os.path.join(dir_name, new_name)

    # os.rename(image_path, new_path)
    print(f"\tRenamed {image_path} -> {new_path}")


def process_images(folder_path):
    """Processes all images in the given folder."""
    # Initialize cache with 4 decimal places precision
    cache = GeocodeCache(tolerance=0.025, decimals=4)

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('jpg', 'jpeg', 'heic')):
                image_path = os.path.join(root, file)

                # Test if image file has already been renamed...
                if '-' in file:
                    print(f"Skipping {image_path} as it has already been renamed.")
                    continue

                print(f"Processing {image_path}...")

                # Extract latitude and longitude from EXIF
                lat_lon = get_lat_lon_from_exif(image_path)
                if lat_lon:
                    lat, lon = lat_lon
                    # print(f"Found coordinates: {lat}, {lon}")

                    # Get city name from coordinates
                    # city_name = get_city_from_lat_lon(lat, lon)
                    city_name = geocode(lat, lon, cache)
                    if city_name:
                        # Rename the file
                        print(f"{image_path}: {city_name}....")
                        rename_image(image_path, city_name)
                    else:
                        print(f"City name not found for {image_path}")
                else:
                    print(f"No EXIF data for coordinates in {image_path}")


def main():
    """Main function to run the script."""
    if len(sys.argv) != 2:
        print("Usage: python rename_images.py <folder_path>")
        sys.exit(1)

    folder_path = sys.argv[1]

    if not os.path.isdir(folder_path):
        print(f"The path '{folder_path}' is not a valid directory.")
        sys.exit(1)

    process_images(folder_path)


if __name__ == "__main__":
    main()
