import json
import requests

import sys
sys.path.append("/home/ubuntu/mark")

from core.utils_api import API_URL, REQUEST_HEADERS

# import image information from json file
def get_images():
    with open('/home/ubuntu/mark/config/settings/db_images.json') as f:
        data = json.load(f)
    return data


# Insert/update docker images in database
def main():
    images = get_images()

    response = requests.post(f"{API_URL}/docker_images/", headers=REQUEST_HEADERS, verify=False, timeout=2*60, json=images)
    response.raise_for_status()

    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        print(f"Error while adding images to database: {ex}")
        exit(1)
