from datetime import date, datetime, time, timedelta
import logging
import os
from google.appengine.ext.ndb import Query
from google.appengine.ext.webapp import template
import webapp2
from download_item import Download
from google.appengine._internal.django.utils import simplejson

__author__ = 'simonhutton'


def extract_data(items):
    uploads = [download for download in items if not download.download]
    downloads = [download for download in items if download.download]

    file_types = ['csv', 'xslx', 'html', 'xml', 'pdf', 'json', 'txt', 'tsv']

    file_type_frequencies = [len([download for download in items if download.extension == extension]) for extension in
                             file_types]

    return {'uploads': len(uploads),
            'downloads': len(downloads),
            'fileTypeFrequencies': file_type_frequencies}

def same_day(date1, date2):
    return date1.year == date2.year and date1.month == date2.month and date1.day == date2.day

def extract_trend_data(items):

    items.sort(key=lambda download_item: download_item.created_date)

    first_date = items[0].created_date
    last_date = items[len(items) - 1].created_date

    current_date = first_date

    uploads = []
    downloads = []
    labels = []

    while current_date < last_date:
        matches = [item for item in items if same_day(current_date, item.created_date)]

        uploads.append(len([match for match in matches if not match.download]))
        downloads.append(len([match for match in matches if match.download]))
        labels.append(current_date.strftime('%a %d %b'))

        current_date = current_date + timedelta(1)

    return labels, uploads, downloads


class Statistics(webapp2.RequestHandler):
    def get(self):
        path = os.path.join(os.path.join(os.path.dirname(__file__), 'html'), '../templates/stats.html')
        self.response.out.write(template.render(path, {}))


class StatisticsData(webapp2.RequestHandler):
    def get(self):
        logging.info('Starting to fetch statistics')

        today = datetime.combine(date.today(), time())
        yesterday = today - timedelta(days=1)
        month_ago = today - timedelta(days=30)

        query = Download.query()

        logging.info('Built query')

        query_options = {'batch_size': 1000}

        all_downloads = query.fetch(**query_options)

        logging.info('Called fetch(**query_options) on query')

        # all_downloads = []

        month_items = [download for download in all_downloads if download.created_date > month_ago]
        yesterday_items = [download for download in month_items if yesterday < download.created_date < today]
        today_items = [download for download in month_items if download.created_date > today]

        logging.info('Sorted results into buckets')

        today_values = extract_data(today_items)
        today_values['title'] = "Today"

        yesterday_values = extract_data(yesterday_items)
        yesterday_values['title'] = "Yesterday"

        month_values = extract_data(month_items)
        month_values['title'] = "Last 30 days"

        logging.info('Extracted today, yesterday and month')

        all_values = extract_data(all_downloads)
        all_values['title'] = "All"

        logging.info('Extracted all')

        trend_labels, trend_uploads, trend_downloads = extract_trend_data(month_items)

        trend_data = {'labels': trend_labels,
                      'uploads': trend_uploads,
                      'downloads': trend_downloads}

        days_data = [today_values,
                     yesterday_values,
                    month_values,
                    all_values]

        response = {'days': days_data,
                    'trend': trend_data}

        self.response.out.write(simplejson.dumps(response))


