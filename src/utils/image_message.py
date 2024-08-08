import os
import base64
from PIL import Image
from copy import deepcopy

def concat_two_images(img1_path, img2_path, output_path):
    # Open the two images
    image1 = Image.open(img1_path)
    image2 = Image.open(img2_path)

    # Get the dimensions of the images
    width1, height1 = image1.size
    width2, height2 = image2.size

    # Define the space between the images
    space = 50

    # Create a new blank canvas with the combined width, maximum height, and white background
    result_width = width1 + width2 + space*3
    result_height = max(height1, height2) + space*2
    result = Image.new('RGB', (result_width, result_height), color='white')

    # Paste the first image on the left side
    result.paste(image1, (50, 50))

    # Paste the second image on the right side with space in between
    result.paste(image2, (width1 + space*2, 50))

    # Save the resulting image
    # result.save("concatenated_image_with_space.png")
    # result.save(f"./images_for_annotation1/{os.path.basename(dir)}.png")
    result.save(output_path)


def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
    

def replace_image_url(messages, throw_details=False, keep_path=False):
    new_messages = deepcopy(messages)
    for message in new_messages:
        if message["role"] == "user":
            if isinstance(message["content"], str):
                continue
            for content in message["content"]:
                if content["type"] == "image_url":
                    image_url = content["image_url"]["url"]
                    image_url_parts = image_url.split(";base64,")
                    if not keep_path:
                        content["image_url"]["url"] = image_url_parts[0] + ";base64," + image_to_base64(image_url_parts[1])
                    else:
                        content["image_url"]["url"] = f"file://{image_url_parts[1]}"
                    if throw_details:
                        content["image_url"].pop("detail", None)
    return new_messages