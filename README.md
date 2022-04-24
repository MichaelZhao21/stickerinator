# Stickerinator!

A small project that I started on a whim when I got annoyed manually cropping images from online. Let's say we had a perfectly cute clipart that we wanted to put into our presentation:

![Pusheen image with (eww) white background](sample-images/pusheen.jpg)

I mean I can boot up good ol' Photoshop, spend a couple minutes fiddling around with the magic select tool, select the background, invert the selection, grow the selection to a couple of pixels, cut the image and paste it on a new file, crop the image, then save it with a transparency layer, **buttttt who wants to do that**??? 

Well, I certainly didn't. So that's why I have this _"simple"_ script that allows you to easily remove the background, crop, and even add a white border to this cute little sticker! Here's the output of my program:

![Nice pusheen sticker!](sample-images/pusheen-after.png)

Pretty good huh! This was all done through a Google Colab notebook, and that's really the only other file in this repo *for now*. I'm hoping to be able to continue this with more features that I'll list below.

## What It Does

So basically this script will remove the background and add a border while cropping it to a normalized size. However, there are some caveats: The input images need to have a **uniform solid-colored background** or else the script cannot floodfill properly. Additionally, the filling algorithm will need to have its threshold adjusted for some images as lighter-colored subjects may not have as well distinguished borders. 

## How to Use

### Jupiter Notebook

Simply open up the notebook in Google Colab and run the 2 function initializers. Then, under the `Runner` section, you can use the `FILE_NAME` variable to set the file name to input. The 2 functions are already written and can be modified as needed to crop your image!

The program should output the images to the `processed` folder on Colab.

### Python Script

To use the script, you need to install all the required packages. The suggested way to do this is in a [virtual environment](https://docs.python.org/3/library/venv.html). Here is the way I would do it: create a venv, activate it, and install packages from `requirements.txt`.

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

To actually run the program, there are a few important folders:

- `/margins` will contain the images outputted by the add margins function
- `/processed` will contain the images outputted by the process images function
- `/image*` contains input images, these folders are user-created (will be excluded from Git) 

> NOTE: To leave the virtual environment, simply type `deactivate`.

## Technologies Used

- **Google Colab**: Great platform for coding and running python notebooks!
- **Numpy**: Although I've touched it in the past, this project has made me much more familiar with manipulating numpy arrays
- **[Python Pillow](https://python-pillow.org/)**: A cool image manipulation tool that made this whole project possible, with tools like actually reading in the image, flood filling an area with color, Gaussian blurs, and so much more!

## Future Ideas/Extensions

- Create a native python script that can be run with any python interpreter (needs command line arguments mostly)
- Add the ability to crop images **without solid light colored background** -> this is very very very hard TT
