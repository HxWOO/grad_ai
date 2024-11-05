# model_runner.py

import os
import time
import numpy as np
import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from options.test_options import TestOptions
from data import create_dataset
from models import create_model
from util.util import tensor2im, save_image, save_depth, decode_labels, depth2normal_ortho
import PIL.Image as Image


def run_model(model_name, dataroot, datalist, results_dir):
    # Set options
    opt = TestOptions().parse()  # get test options
    opt.model = model_name
    opt.dataroot = dataroot
    opt.datalist = datalist
    opt.results_dir = results_dir

    # make destination dirs.
    os.makedirs(results_dir, exist_ok=True)
    if 'MTM' in opt.model:
        os.makedirs(os.path.join(results_dir, 'warp-cloth'), exist_ok=True)
        os.makedirs(os.path.join(results_dir, 'warp-mask'), exist_ok=True)
        os.makedirs(os.path.join(results_dir, 'warp-grid'), exist_ok=True)
        os.makedirs(os.path.join(results_dir, 'warp-cloth-sobel'), exist_ok=True)
        os.makedirs(os.path.join(results_dir, 'segmt'), exist_ok=True)
        os.makedirs(os.path.join(results_dir, 'segmt-vis'), exist_ok=True)
        os.makedirs(os.path.join(results_dir, 'initial-depth'), exist_ok=True)
        os.makedirs(os.path.join(results_dir, 'initial-depth-vis'), exist_ok=True)
        os.makedirs(os.path.join(results_dir, 'initial-normal-vis'), exist_ok=True)
    if 'TFM' in opt.model:
        os.makedirs(os.path.join(results_dir, 'tryon'), exist_ok=True)
    if 'DRM' in opt.model:
        os.makedirs(os.path.join(results_dir, 'final-depth'), exist_ok=True)
        os.makedirs(os.path.join(results_dir, 'final-depth-vis'), exist_ok=True)
        os.makedirs(os.path.join(results_dir, 'final-normal-vis'), exist_ok=True)

    # hard-code some parameters for test
    opt.num_threads = 1  # test code only supports num_threads = 1
    opt.batch_size = 1  # test code only supports batch_size = 1
    opt.serial_batches = True  # disable data shuffling
    dataset = create_dataset(opt)  # create a dataset given opt.dataset_mode and other options
    dataset_size = len(dataset)
    model = create_model(opt)  # create a model given opt.model and other options
    model.setup(opt)  # regular setup: load and print networks

    # test with eval mode.
    if opt.eval:
        model.eval()

    for i, data in enumerate(dataset):
        if i >= opt.num_test:  # only apply our model to opt.num_test images.
            break
        model.set_input(data)  # unpack data from data loader
        model.test()  # run inference
        im_name = model.im_name[0]  # get person name
        c_name = model.c_name[0]  # get cloth name
        print('processing (%04d)-th / (%04d) image...' % (i + 1, dataset_size), end='\r')
        time.sleep(0.001)

        # Your existing processing code follows...

    print(f'\nTesting {opt.model} finished.')
