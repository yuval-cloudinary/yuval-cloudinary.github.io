# cSpell:words Zapier, rfind
"""
This script is about flow automation:
 1. Input: a Dropbox URL of a folder with images
 2. Pick up few images which have suffix from a predefined list
 3. Upload the images to cld
 4. Output: A cld image of a collage of the previously selected images


The script was written without SDK with a thought to execute it via Zapier Code block
"""

# cSpell: ignore urlunparse
import requests
import io
import zipfile
from urllib.parse import urlparse, urlunparse
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
import base64
import re
import argparse
import sys
from socket import timeout

# input_data variable is used for Zapier integration
if not 'input_data' in locals():
    parser = argparse.ArgumentParser(
        description="This script would import a shared Dropbox folder to Cloudinary, and would download a collage strip of chosen images")
    parser.add_argument('--dropbox_link', '-d', metavar='', type=str,
                        help='A URL link to a shared folder on Dropbox with required images')
    parser.add_argument('--cloudinary_root_folder', '-c', metavar='', default='', type=str,
                        help='A folder on Cloudinary to upload the assets under. Default is under the root folder')
    parser.add_argument('--ordered_suffixes', '-s', metavar='', default='000A,030A,090A,270A,330A', type=str,
                        help='Image suffixes to use in the collage strip (comma seprated list)')
    parser.add_argument('--width', '-w', metavar='', default='1500', type=str,
                        help='Collage width in pixels. Default is 1500')
    parser.add_argument('--height', '-e', metavar='', default='700', type=str,
                        help='Collage height in pixels. Default is 700')
    parser.add_argument('--download_name', '-o', metavar='', default='strip.jpg', type=str,
                        help="Output to a specific file. Default is 'strip.jpg' in current folder")

    input_data = vars(parser.parse_args())
    if not input_data['dropbox_link']:
        parser.print_help(sys.stderr)
        sys.exit(1)

# Cloud name is hardcoded by design
cloudinary_api_base = 'https://api.cloudinary.com/v1_1/papish/image/upload'
dropbox_link = input_data['dropbox_link']
# each set of images is uploaded to its own folder

cloudinary_root_folder = '/'
if 'cloudinary_root_folder' in input_data and input_data['cloudinary_root_folder'] > '':
    cloudinary_root_folder = input_data['cloudinary_root_folder']
cloudinary_folder = cloudinary_root_folder + \
    dropbox_link.split('/')[-1].split('?')[0]


def validate_relative_path(filename):
    """
    Protection against path traversal attack
    """

    filename = filename.lstrip()
    if (filename.startswith('/')):
        return 'Download name cannot starts with a slash'
    if (filename.rfind(':', 0, 5) > -1):
        return 'Download name cannot have colon in the first 6 chars'
    return 'valid'


def upload_cloudinary(file_name, image):
    """
    Using direct API call saves the hassle of 
    maintaining Cloudinary SDK on Lambda
    Zapier, doesn't support the SDK package at all
    """

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        # 'Content-Type': 'application/octet-stream',
    }
    img_file = io.BytesIO(image)
    img_file.name = 'file'
    payload = {
        'file': "data:{};base64,{}".format('image/jpeg', base64.b64encode(image).decode()),
        # 'file': img_file,
        'upload_preset': 'glasses_strip',
        'public_id': cloudinary_folder + '/' + file_name[: file_name.rfind('.')]
    }

    url = cloudinary_api_base
    response = requests.post(url, headers=headers, data=payload)
    response.raise_for_status()
    return response.json()


def process_zip_file(dropbox_link):
    """
    Downloading a zipped folder from Dropbox.
    Then, doing in memory extraction and filtering of the downloaded ZIP.
    """

    downloadable_dropbox_folder = urlunparse(
        urlparse(dropbox_link)._replace(query='dl=1'))
    raw_zip = requests.get(downloadable_dropbox_folder)
    zipfile_obj = zipfile.ZipFile(io.BytesIO(raw_zip.content))
    suffix_zip_array = []

    for zipinfo in zipfile_obj.infolist():
        for suffix in input_data['ordered_suffixes'].split(','):
            if suffix == '':
                continue
            if zipinfo.filename.find('_' + suffix + '.') > -1:
                upload_response = upload_cloudinary(
                    zipinfo.filename, zipfile_obj.read(zipinfo))
                suffix_zip_array.append(
                    [suffix, zipinfo, upload_response['secure_url']])

    zipfile_obj.close()
    return suffix_zip_array


def cld_request_builder(cld_urls):
    """
    Based on the array of the collage images,
    overlay the first N-1 images on the Nth image.
    Use SEO naming based on input argument
    """

    i = 0
    helper_pattern = re.compile(r"(^.*image/upload/v\d+/)(.*)(\.\w+$)")
    # Usage of cld variables, creates a more human-friendly dynamic transformations
    overlayed_images = 'images/fl_attachment,$w_' + \
        input_data['width'] + ',$h_' + \
        input_data['height'] + ',c_pad,w_$w,h_$h/'
    while i < len(cld_urls) - 1:
        try:
            url2overlay = 'l_' + \
                helper_pattern.match(cld_urls[i][2])[2].replace('/', ':')
            overlayed_images += url2overlay + '/c_pad,w_$w,h_$h/g_west,x_w,fl_layer_apply/'
        except:
            print('Image "' + cld_urls[i][2] +
                  '" is skipped: Unexpected URL format')
        i += 1
    seo_name = input_data['download_name'].split('/')[-1]
    cld_last_image_secure_url = cld_urls[i][2][: cld_urls[i][2].rfind('.')]
    return re.sub(
        r"image/upload/v\d+\/",
        overlayed_images,
        cld_last_image_secure_url) + "/" + seo_name


def download_strip(url):
    """
    Downloading the image when ran from CLI
    """
    try:
        img = urlopen(url)
        with open(input_data['download_name'], 'wb') as f:
            f.write(img.read())
    except (HTTPError, URLError) as error:
        return {'error': url + ' could not be opened. Error: ' + str(error)}
    except timeout:
        return {'error': 'socket timed out - URL ' + url}
    except Exception as error:
        return {'error': 'Error: ' + str(error)}


# output variable is used for Zapier integration
output = validate_relative_path(input_data['download_name'])
if output == 'valid':
    suffix_zip_array = []
    try:
        suffix_zip_array = process_zip_file(dropbox_link)
    except Exception as e:
        output = {'error': 'Dropbox folder was not found or failed to extract'}
    if output == 'valid':
        if len(suffix_zip_array) < 2:
            output = {'error': "Not enough photos for a collage. Need at least 2 photos. " +
                      str(len(suffix_zip_array)) + " was identified."}
        else:
            download_strip(output)
            output = {'download': cld_request_builder(suffix_zip_array)}
