import json
import string
from google.appengine.api.app_identity import app_identity

import time
from palette_reader import process_aco

__author__ = 'simonhutton'

import sys

sys.path.insert(0, 'libs')

import conversion

import webapp2

import hashlib
from google.appengine.ext import blobstore
import logging
import cloudstorage as gcs
from helper import log_upload, support_email, process_colors
from google.appengine._internal.django.utils import simplejson
import traceback
import io


def drop_extension_from_filename(filename):
    sp = filename.split('.')

    if len(sp) > 1:
        return string.join(sp[:-1], '.')
    else:
        return filename


class Upload(webapp2.RequestHandler):
    @staticmethod
    def get_conversion_from_hash(file_hash):
        query = conversion.Conversion.gql("WHERE hash = :hash", hash=file_hash)
        conversions = query.fetch(1)
        if conversions:
            return conversions[0]
        else:
            return None

    @staticmethod
    def save_file(file_hash, file_content):
        blob_filename = '/%s/%s/%s' % (app_identity.get_default_gcs_bucket_name(), 'ics', file_hash)
        with gcs.open(blob_filename, 'w') as f:
            f.write(file_content)

        blob_store_filename = '/gs' + blob_filename
        return blobstore.create_gs_key(blob_store_filename)

    def post(self):

        if len(self.request.params.multi.dicts) > 1 and 'file' in self.request.params.multi.dicts[1]:
            file_info = self.request.POST['file']

            filename = file_info.filename
            file_content = file_info.file.read()
            file_size = len(file_content)
            file_hash = hashlib.md5(file_content).hexdigest()

            try:
                current_conversion = self.get_conversion_from_hash(file_hash)

                start_time = time.time()

                if not current_conversion:
                    # noinspection PyBroadException
                    try:
                        swatches = process_aco(file_content)

                        colors = process_colors(swatches)
                    except Exception, e:
                        colors = None
                        logging.warn('Could not convert "' + filename + '".')
                        logging.warn(e.message)

                    if colors:
                        current_conversion = conversion.Conversion()

                        current_conversion.hash = file_hash
                        current_conversion.filename = filename
                        current_conversion.file_size = file_size
                        current_conversion.color_count = len(swatches)

                        current_conversion.blob_key = self.save_file(file_hash, file_content)

                        current_conversion.put()

                        response = {'message': "Calendar created.",
                                    'key': current_conversion.hash,
                                    'palette': {'filename': current_conversion.filename,
                                                'colors': colors}}

                        logging.info('Uploaded "' + current_conversion.filename + '" with ' + str(current_conversion.color_count) + ' colors.')
                        log_upload(current_conversion, time.time() - start_time)
                    else:
                        # Not a valid iCalendar
                        response = {'message': "That's not a valid aco file.",
                                    'filename': None,
                                    'paid': False,
                                    'key': None}

                        self.response.status = 500
                else:
                    filename = drop_extension_from_filename(filename)

                    if current_conversion.filename != filename:
                        current_conversion.filename = filename

                        current_conversion.put()

                    colors = current_conversion.get_palette()

                    response = {'message': "Existing palette.",
                                'key': current_conversion.hash,
                                'palette': {'filename': current_conversion.filename,
                                                'colors': colors}}

                    log_upload(current_conversion, time.time() - start_time)
            except Exception, e:
                trace = traceback.format_exc()

                logging.error('Exception while tyring to upload.')
                logging.error(e.message)
                logging.error(trace)

                email_message = e.message + '\r\n\r\n' + trace

                support_email('Upload Failed', email_message)

                response = {'message': "Something bad happened, we're looking at it."}

                self.response.status = 500
        else:
            response = {'message': "Something bad happened, we're looking at it."}

            logging.error(self.request.params.multi)

            if len(self.request.params.multi) > 0:
                support_email('Upload Failed', str(self.request.params.multi))

            self.response.status = 500

        self.response.out.write(simplejson.dumps(response))

