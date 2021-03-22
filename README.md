# Semi-Auto-Annotation-Tool-for-Image-Anomaly-Detection
This is Semi Auto Annotation Tool for Image Anomaly Detection.

## What is it?

This program will collect negative/positive image patches.

Input : your effort for drawing some polygons

Output : negative/positive sample image patches, mask images, annotations

## requirements

- PyQt5

- opencv-python

- numpy

## How to use

### Setting

- `python Annotator.py`

- First, choose a directory contains more than one image.

- Second, adjust canvas size. It depends on your monitor resolution.

- Third, click start cropping button.

### Cropping

- You can draw polygons on the canvas.
- You can adjust crop size and stride. Try example button.
- Click Go! button to automatically crop the image.
- The result will be saved under `results/{image directory}`. There will be `annotations`,  `mask`, `neg_mask`, `negative`, `positive` directories.

## Demo

<img src="doc/using.gif"/>

## End

If you have any trouble using this program, please use issue tab.

Thank you.

## License
MIT License

Copyright (c) 2021 ZeroAct

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.