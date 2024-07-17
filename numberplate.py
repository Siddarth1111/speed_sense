def plate_recognition(img):
    import requests
    # import cv2  # Assuming you are using OpenCV for image operations

    # Example 1: Uploading an image from a file path
    # regions = ["mx", "us-ca"]  # Define your regions
    image_path = img  # Update with your image file path

    with open(image_path, 'rb') as fp:
        response = requests.post(
            'https://api.platerecognizer.com/v1/plate-reader/',
            # data=dict(regions=regions),  # Optional: Specify regions
            files=dict(upload=fp),
            headers={'Authorization': 'Token #yourtokenhere#'}
        )

    result = response.json()
    plate = result['results'][0]['plate'].upper()

    return plate
