import StringIO
import logging
import os
import sys
import time
import traceback
from google.appengine.api import memcache
from google.appengine.runtime import DeadlineExceededError
from helper import process_calendar, log_download, support_email, format_events_for_html, format_events_for_txt

sys.path.insert(0, 'libs')

import re
import webapp2
import conversion
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import template
from google.appengine._internal.django.utils import simplejson

__author__ = 'simonhutton'

column_order = ['Summary', 'Description', 'Start', 'End', 'Organizer', 'Attendees', 'Location', 'Created']


def order_columns(column_name, keys):
    return column_name in keys


def build_tab_lib_dataset(events):
    data = None #tablib.Dataset()

    keys = list(set([key for event in events for key in event.keys()]))

    ordered_columns = [item for item in column_order if order_columns(item, keys)]

    rows = [[event.get(key, '') for key in ordered_columns] for event in events]

    data.headers = ordered_columns

    for row in rows:
        data.append(row)

    return data


def generate_csv_content(events):
    data = build_tab_lib_dataset(events)

    return data.csv


def generate_xls_content(events):
    data = build_tab_lib_dataset(events)

    return data.xls


def generate_xlsx_content(events):
    data = build_tab_lib_dataset(events)

    return data.xlsx


def generate_json_content(events):
    data = build_tab_lib_dataset(events)

    return data.json


def generate_tsv_content(events):
    data = build_tab_lib_dataset(events)

    return data.tsv


def generate_txt_content(events):
    path = os.path.join(os.path.join(os.path.dirname(__file__), 'html'), '../templates/txt_template.txt')

    events = format_events_for_txt(events)

    return template.render(path, {'events': events})


def generate_xml_content(events):
    path = os.path.join(os.path.join(os.path.dirname(__file__), 'html'), '../templates/xml_template.xml')

    return template.render(path, {'events': events})


def generate_html_content(events, filename, event_count):
    path = os.path.join(os.path.join(os.path.dirname(__file__), 'html'), '../templates/html_template.html')

    events = format_events_for_html(events)

    return template.render(path, {'events': events, 'filename': filename, 'event_count': event_count})


class Downloading(webapp2.RequestHandler):
    @staticmethod
    def get_conversion_from_hash(file_hash):
        query = conversion.Conversion.gql("WHERE hash = :hash", hash=file_hash)
        conversions = query.fetch(1)
        if conversions:
            return conversions[0]
        else:
            return None

    def get(self):

        # noinspection PyBroadException
        try:
            matches = re.match(
                r"/download/(?P<hash>[0-9a-z]+)/(?P<filename>[-\w^&'@{}[\],$=!#().%+~ ]+).(?P<extension>txt|csv|xlsx|xls|json|tsv|xml|html|pdf)",
                self.request.path)

            if matches:
                file_hash = matches.group("hash")
                filename = matches.group("filename")
                extension = matches.group("extension")

                download_id = file_hash + '.' + extension

                self.response.set_cookie(download_id)

                start_time = time.time()

                current_conversion = self.get_conversion_from_hash(file_hash)

                if file_hash == 'sample':
                    path = os.path.join(os.path.join(os.path.dirname(__file__), 'html'), '../templates/error.html')
                    self.response.out.write(template.render(path, {'status': '???',
                                                                   'message': "Upload a valid .ics file and we'll<br/>convert it to .csv, .xlsx, .html or .pdf."}))

                    self.response.status = 200
                else:
                    if current_conversion:
                        events = current_conversion.get_events()

                        self.response.headers['Content-Transfer-Encoding'] = 'binary'
                        self.response.headers['Accept-Range'] = 'bytes'
                        self.response.headers['Content-Length'] = str(current_conversion.file_size)
                        self.response.headers['Content-Encoding'] = 'binary'
                        self.response.headers['Content-Disposition'] = 'attachment; filename=' + filename + '.' + extension

                        if extension == 'csv':
                            self.response.headers['Content-Type'] = 'application/csv'
                            output_content = generate_csv_content(events)

                            log_download(current_conversion, time.time() - start_time, extension)

                            logging.info('Downloaded "' + filename + '.' + extension + '" with ' + str(current_conversion.event_count) + ' events.')

                            self.response.out.write(output_content)
                        else:
                            output_content = "saf"

                            if current_conversion.paid_date:
                                if extension == 'xls':
                                    self.response.headers['Content-Type'] = 'application/xls'
                                    output_content = generate_xls_content(events)

                                if extension == 'xlsx':
                                    self.response.headers['Content-Type'] = 'application/xlsx'
                                    output_content = generate_xlsx_content(events)

                                if extension == 'json':
                                    self.response.headers['Content-Type'] = 'application/json'
                                    output_content = generate_json_content(events)

                                if extension == 'tsv':
                                    self.response.headers['Content-Type'] = 'application/tsv'
                                    output_content = generate_tsv_content(events)

                                if extension == 'txt':
                                    self.response.headers['Content-Type'] = 'application/txt'
                                    output_content = generate_txt_content(events)

                                if extension == 'xml':
                                    self.response.headers['Content-Type'] = 'application/xml'
                                    output_content = generate_xml_content(events)

                                if extension == 'html':
                                    self.response.headers['Content-Type'] = 'application/html'
                                    output_content = generate_html_content(events, filename + '.' + extension, current_conversion.event_count)

                                log_download(current_conversion, time.time() - start_time, extension)
                                logging.info('Downloaded "' + filename + '.' + extension + '" with ' + str(current_conversion.event_count) + ' events.')

                                self.response.out.write(output_content)
                            else:
                                support_email('Download Failed',
                                              "Trying to download file type (" + extension + ") which hasn't been paid for, hash: " + file_hash)

                                logging.warn(
                                    "Trying to download file type (" + extension + ") which hasn't been paid for, hash: " + file_hash)

                                path = os.path.join(os.path.join(os.path.dirname(__file__), 'html'), '../templates/error.html')
                                self.response.out.write(template.render(path, {'status': '404',
                                                                               'message': "We don't have what you're looking for."}))

                                self.response.status = 404
                    else:
                        support_email('Download Failed', 'Could not find hash: ' + file_hash)

                        logging.warn('Could not find hash: ' + file_hash)

                        path = os.path.join(os.path.join(os.path.dirname(__file__), 'html'), '../templates/error.html')
                        self.response.out.write(template.render(path, {'status': '404',
                                                                       'message': "We don't have what you're looking for."}))

                        self.response.status = 404
            else:
                matches = re.match(
                    r"/download/(?P<hash>[0-9a-z]+)",
                    self.request.path)

                if matches:
                    logging.warn('Could not parse path: ' + self.request.path + ' redirecting.')

                    file_hash = matches.group("hash")

                    self.redirect("/" + file_hash)
                else:
                    support_email('Download Failed', 'Could not parse path: ' + self.request.path)

                    logging.warn('Could not parse path: ' + self.request.path)

                    path = os.path.join(os.path.join(os.path.dirname(__file__), 'html'), '../templates/error.html')
                    self.response.out.write(template.render(path, {'status': '404',
                                                                   'message': "We don't have what you're looking for."}))

                    self.response.status = 404
        except DeadlineExceededError, e:
            trace = traceback.format_exc()

            logging.error(e.message)
            logging.error(trace)

            email_message = self.request.path + '\r\n\r\n' + e.message + '\r\n\r\n' + trace

            support_email('DeadlineExceededError', email_message)

            path = os.path.join(os.path.join(os.path.dirname(__file__), 'html'), '../templates/error.html')
            self.response.out.write(template.render(path, {'status': '500',
                                                           'message': "Something bad happened, we're looking at it."}))

            self.response.status = 500
        except Exception, e:
            trace = traceback.format_exc()

            logging.error(e.message)
            logging.error(trace)

            email_message = e.message + '\r\n\r\n' + trace

            support_email('Download Failed', email_message)

            path = os.path.join(os.path.join(os.path.dirname(__file__), 'html'), '../templates/error.html')
            self.response.out.write(template.render(path, {'status': '500',
                                                           'message': "Something bad happened, we're looking at it."}))

            self.response.status = 500
