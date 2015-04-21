#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import json
import logging
import sys
import datetime
import re
from configuration import Configuration
from helper import format_events_for_html
import statistics

import upload


sys.path.insert(0, 'libs')

import conversion
import downloading

import os
from google.appengine.ext.webapp import template
import webapp2
from google.appengine._internal.django.utils import simplejson


def get_conversion_from_hash(file_hash):
    query = conversion.Conversion.gql("WHERE hash = :hash", hash=file_hash)
    conversions = query.fetch(1)
    if conversions:
        return conversions[0]
    else:
        return None


class Home(webapp2.RequestHandler):
    def get(self):

        config = Configuration.get_instance()

        example_palette = [{'name': 'blue',
                            'hex': ''}]

        path = os.path.join(os.path.join(os.path.dirname(__file__), 'html'), '../templates/main.html')
        self.response.out.write(template.render(path, {'show_file': False,
                                                       'stripe_key': config.public_stripe_key,
                                                       'web_debug': config.web_debug}))


class ShowFile(webapp2.RequestHandler):
    def get(self):

        config = Configuration.get_instance()

        matches = re.match(
            r"/(?P<hash>[0-9a-z]+)",
            self.request.path)

        if matches:
            file_hash = matches.group("hash")

            current_conversion = get_conversion_from_hash(file_hash)

            if current_conversion:

                path = os.path.join(os.path.join(os.path.dirname(__file__), 'html'), '../templates/main.html')

                palette = current_conversion.get_palette()

                self.response.out.write(template.render(path, {'show_file': True,
                                                                'key': current_conversion.hash,
                                                                'filename': current_conversion.filename,
                                                                'full_filename': current_conversion.full_filename,
                                                                'palette': palette,
                                                                'web_debug': config.web_debug}))
                return

        path = os.path.join(os.path.join(os.path.dirname(__file__), 'html'), '../templates/error.html')
        self.response.out.write(template.render(path, {'status': '404',
                                                       'message': "We don't have what you're looking for."}))

        self.response.status = 404




class What(webapp2.RequestHandler):
    def get(self):

        path = os.path.join(os.path.join(os.path.dirname(__file__), 'html'), '../templates/what.html')
        self.response.out.write(template.render(path, {}))


app = webapp2.WSGIApplication([('/', Home),
                               ('/upload', upload.Upload),
                               ('/download/.*', downloading.Downloading),
                               ('/what-is-a-ics-file', What),
                               ('/statistics', statistics.Statistics),
                               ('/statistics-data', statistics.StatisticsData),
                               ('/.*', ShowFile)], debug=True)
