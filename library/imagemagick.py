#! /usr/bin/env python
# coding=utf-8
__author__ = 'Xuxh'

import subprocess


def execute_cmds(cmds,debug=False):

    ret = ''
    if type(cmds) == str:
        cmds = [cmds]
    for cmd in cmds:
        if debug:
            print 'Execute command: {}'.format(cmd)
        ret = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        ret.wait()
        if ret.returncode != 0:
            return ret
    return ret


def crop_image(img_path, width, height, x, y, output_path='crop_img.jpg'):
    cmds = [
    'convert {}[{}x{}+{}+{}] {}'.format(img_path, width, height, x, y,
                                        output_path)
    ]
    ret = execute_cmds(cmds)
    return ret


def resize_image(img_path, width, height, output_path):
    cmds = [
    'convert {} -resize {}x{} {}'.format(img_path, width, height, output_path)
    ]
    ret = execute_cmds(cmds)
    return ret


def identify_image(img_path):

    cmds = ['identify {}'.format(img_path)]
    ret = execute_cmds(cmds)
    return ret


def make_image_gray(img_path, gray_img):
    cmds = [
        'convert {} -type Grayscale -depth 4 {}'.format(img_path, gray_img),
    ]
    ret = execute_cmds(cmds)
    return ret


# the most better method to make gray image at first, then compare
def compare_image(actu_image,expe_image):

    cmds = [
    'compare -metric AE -fuzz 20% {} {} similar.jpg'.format(actu_image, expe_image),
    ]
    ret = execute_cmds(cmds)
    if ret.returncode != 0:
        return False
    else:
        value = int(ret.stdout.readline())
        if value < 2000:
            return True
        else:
            return False


def detect_sub_image(sub_img_path, sub_x, sub_y, search_img_path,
                 search_width, search_height, search_x, search_y):

    sub_gray_img = 'sub_gray_img.jpg'
    search_gray_img = 'search_gray_img.jpg'
    crop_img = 'crop_img.jpg'

    ret = make_image_gray(sub_img_path, sub_gray_img)
    if ret.status_code != 0:
        return False

    ret = make_image_gray(search_img_path, search_gray_img)
    if ret.status_code != 0:
        return False

    ret = crop_image(search_gray_img, search_width, search_height, search_x,
                     search_y)
    if ret.status_code != 0:
        return False

    cmds = [
        'compare -channel black -metric RMSE -subimage-search {} {} similar.png'.
        format(crop_img, sub_gray_img)
    ]

    # see if the v logo detection is correct
    ret = execute_cmds(cmds)
    if ret.status_code != 0:
        return False
    ret_str = ret.std_err
    pos_x, pos_y = [int(x) for x in ret_str.split(' ')[-1].split(',')]
    if pos_x != (sub_x - search_x) or pos_y != (sub_y - search_y):
        return False

    return True
