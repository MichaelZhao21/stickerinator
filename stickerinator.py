import math
from PIL import Image, ImageFilter, ImageDraw
import numpy as np
import re
import os
import sys
from colorama import Fore, Style


ERROR_MESSAGE = f'{Fore.RED}Usage: {sys.argv[0]} <mode>\n\tModes: 0 - Full process, 1 - Add margins only, 2 - No margin processing{Style.RESET_ALL}'


def add_margin(filename):
    """
    Add margins to a picture; this will use the average color of the corners
    for the background color of the margins.
    """

    # Read in the image file
    imr = Image.open(filename).convert('RGBA')
    imr_back = Image.new('RGBA', imr.size, (255, 255, 255))
    imc = Image.alpha_composite(imr_back, imr)
    im = imc.convert('RGB')
    ima = np.array(im)

    # Apply a gaussian blur using 1% of the pixels (this number must be odd w/ min of 1)
    blur_px = max(round(min(im.size[0], im.size[1]) * 0.01), 1)
    imb = im.filter(ImageFilter.GaussianBlur(radius=2))
    imba = np.array(imb)

    # Show images metadata
    print('Original image dims:', im.size[1], 'x', im.size[0])
    print('Blurred with', blur_px, 'x', blur_px, 'Gaussian filter')

    # Utility function to round to the 10s place
    ceil_tens = np.vectorize(lambda x: min(math.ceil(x / 10) * 10, 250))

    # Calculate how many pixels to get (~5% of the length of the shortest side)
    width = im.size[0]
    height = im.size[1]
    px = round(min(width, height) * 0.05)

    # Get corners, where corners are stored in clockwise order starting from the top left
    corners = np.zeros((4, px, px, 3))
    corners[0] = imba[:px, :px]
    corners[1] = imba[:px, -px:]
    corners[2] = imba[-px:, :px]
    corners[3] = imba[-px:, -px:]

    # We first want to store all counts of color values in a dictionary
    # Rounding the values to the tens place allows for us to correct for slight changes in color
    # If there is a color that has a majority in the dictionary, it is probably the background color
    corner_list = np.reshape(corners, (px * px * 4, 3))
    rounded_corner_list = ceil_tens(corner_list)
    corner_dict = {}
    for item in rounded_corner_list:
        item_t = tuple(item)
        if item_t in corner_dict.keys():
            corner_dict[item_t] = corner_dict[item_t] + 1
        else:
            corner_dict[item_t] = 1

    # Sort the dictionary to get the most common color among all these pixels
    corner_dict_sorted = dict(
        sorted(corner_dict.items(), key=lambda item: -item[1]))
    color_list = list(corner_dict_sorted.keys())
    bg = color_list[0]

    color_img = np.empty((40, 40, 3), np.uint8)
    color_img[:, :] = bg

    clist_img = np.empty((20, 20 * len(color_list), 3), np.uint8)
    for i, val in enumerate(color_list):
        clist_img[:, (i*20):((i+1)*20)] = val

    print('Approx corner color counts:', corner_dict_sorted)
    print('Most common (probably background) color:', bg)

    # Expand the edges of the image by 10% of the longest edge with the background
    # color as the fill color.
    mg = round(max(width, height) * 0.1)
    exp_img = np.full((height+(2*mg), width+(2*mg), 3), bg, np.float32)
    exp_img[mg:(height+mg), mg:(width+mg)] = ima
    ei = Image.fromarray((exp_img).astype(np.uint8))

    print('\nAdded', mg, 'pixel margin to edges:')

    # Save
    fn_no_pre = re.sub('^.*\/', '', filename)
    path = f'margins/exp-{fn_no_pre}'
    ei.save(path)
    return path


def process_img(filename, add_border, crop, threshold=150):
    """
    Processes images by creating a floodfill seed from the (10, 10) pixel,
    floodfilling to find the edges of the subject, creating a border from
    those edges, and combining the floodfill/border mask to create a
    masking of the original image. This mask will be applied to the
    original image to make background pixels transparent. This function
    will also crop the image if the crop param is true.
    """

    # Read in the image file
    im = Image.open(filename).convert('RGB')

    # Floodfill op
    print('\nCreating image mask...')
    ImageDraw.floodfill(im, xy=(10, 10), value=(255, 0, 255), thresh=threshold)

    # Mask
    am = np.array(im)
    am[(am[:, :, 0:3] != [255, 0, 255]).any(2)] = [0, 255, 0]
    mask = Image.fromarray(am)
    print('Finished image mask!')

    if add_border:
        # Border checking function
        maa = [255, 0, 255]
        def is_border(r, c): return (am[r, c] != maa).any() and ((am[r-1, c] == maa).all() or (
            am[r, c+1] == maa).all() or (am[r+1, c] == maa).all() or (am[r, c-1] == maa).all())

        # Find and draw borders on mask
        draw = ImageDraw.Draw(mask)
        RAD = 8  # Border radius
        print()
        for r in range(1, am.shape[0] - 1):
            for c in range(1, am.shape[1] - 1):
                if is_border(r, c):
                    draw.ellipse((c-RAD, r-RAD, c+RAD, r+RAD),
                                 (0, 255, 0), None)
            print(f'Adding borders on mask... Processing row: {r}/{am.shape[0]}', end='\r')
        print(f'Adding borders on mask... Processing row: {am.shape[0]}/{am.shape[0]}... Done!', end='\n')

        # Add the 2 masks together
        print('\nCombining masks...', end='\r')
        ma = np.array(mask)
        ma = ma + am

        # Fix overflowed color values to 255
        def fix(x): return 255 if x > 0 else 0
        fixv = np.vectorize(fix)
        bma = fixv(ma)

        # Overwrite bm and display
        mask = Image.fromarray(bma.astype(np.uint8))
        print('Combining masks... Done!')

    # Apply mask to original image
    print('\nApplying mask to original image...')
    im.putalpha(255)
    imm = np.array(im)
    bma = np.array(mask)
    imm[(bma[:, :, 0:3] == [255, 255, 255]).all(2)] = [255, 255, 255, 255]
    imm[(bma[:, :, 0:3] == [255, 0, 255]).all(2)] = [0, 0, 0, 0]
    print('Finished masking original image!')
    fim = Image.fromarray(imm)

    # Crop the image
    if crop:
        # Get the max/min x/y of the image
        maa = [255, 0, 255]
        maxh, maxw, minh, minw = 0, 0, am.shape[0], am.shape[1]
        print('\nGetting image bounds...')
        for r in range(1, am.shape[0] - 1):
            for c in range(1, am.shape[1] - 1):
                if (bma[r, c] != maa).any():
                    if maxh < r:
                        maxh = r
                    if minh > r:
                        minh = r
                    if maxw < c:
                        maxw = c
                    if minw > c:
                        minw = c

        # Add 5% margin to the base crop
        mg = round(max(maxw - minw, maxh - minh) * 0.05)
        print(f'Image bounds are (x, y): ({minw}, {minh}) to ({maxw}, {maxh})')
        print('Cropping to bounds with', mg, 'px margin...')
        minw = max(0, minw - mg)
        minh = max(0, minh - mg)
        maxw = min(am.shape[1], maxw + mg)
        maxh = min(am.shape[0], maxh + mg)

        # Actually crop the image
        print('Cropping bounds (x, y, dx, dy):',
              (minw, minh, maxw - minw, maxh - minh))
        fim = fim.crop((minw, minh, maxw, maxh))
        print('Finished cropping image! Cropped size:', fim.size)

    # Save final image
    fn_no_ext = re.sub('\..*$', '', filename)
    fn_no_ext_pre = re.sub('^.*/', '', fn_no_ext)
    fim.save(f'processed/done-{fn_no_ext_pre}.png')


def createDir(name):
    try:
        os.mkdir(name)
        print(f'Created {name} directory!')
    except:
        print(f'{name} directory already exists')


def walk_folder(dirname, func):
    for root, _, files in os.walk(dirname):
        for filename in files:
            full_filename = os.path.join(root, filename)
            func(full_filename)


def full_process(filename):
    margin_filename = add_margin(filename)
    process_img(margin_filename, add_border=True, crop=True)


def main():
    # Check for the correct command line arguments
    if len(sys.argv) < 2:
        print(ERROR_MESSAGE)
        exit(0)
    
    # Create directories
    print(Fore.YELLOW + 'Creating directories...' + Style.RESET_ALL)
    createDir('margins')
    createDir('processed')
    createDir('input')
    print(Fore.YELLOW + 'Directories Created!\n' + Style.RESET_ALL)

    # Process images by mode
    if sys.argv[1] == '0':
        walk_folder('input', full_process)
    elif sys.argv[1] == '1':
        walk_folder('input', add_margin)
    elif sys.argv[1] == '2':
        print(ERROR_MESSAGE)


# Call the main function!
main()
