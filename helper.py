import logging
import sys
from types import *
from google.appengine.api import mail
import download_item

sys.path.insert(0, 'libs')

from google.appengine.ext import ndb


def log_upload(current_conversion, time):
    new_upload = download_item.Download()

    new_upload.download = False
    new_upload.hash = current_conversion.hash
    new_upload.filename = current_conversion.filename
    new_upload.file_size = current_conversion.file_size
    new_upload.time = time

    new_upload.put()


def log_download(current_conversion, time, extension):
    new_download = download_item.Download()

    new_download.download = True
    new_download.hash = current_conversion.hash
    new_download.filename = current_conversion.filename
    new_download.file_size = current_conversion.file_size
    new_download.time = time
    new_download.extension = extension

    new_download.put()


def support_email(subject, message):
    mail.send_mail(sender="ICS Convert Support <simon.hutton@gmail.com>",
                   to="Simon <simon.hutton@gmail.com>",
                   subject=subject,
                   body=message)


def make_safe_name(name):
    return name.replace(" ", "_").lower()


def process_colors(swatches):
    palette = []

    for swatch in swatches:
        palette.append({'name': swatch.name,
                        'safeName': make_safe_name(swatch.name),
                        'hex': swatch.getRGB()})

    return palette