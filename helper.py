import logging
import sys
from types import *
from google.appengine.api import mail
import download_item

sys.path.insert(0, 'libs')

from google.appengine.ext import ndb


def add_text_field(component, component_name, dict, dict_name):
    value = component.get(component_name)

    if value:
        dict[dict_name] = unicode(value)


def add_date_field(component, component_name, dict, dict_name):
    value = component.get(component_name)

    if not isinstance(value, (list, tuple)):
        if value:
            dict[dict_name] = str(value.dt)
    else:
        logging.warn('Got a list as a date field')
        logging.warn(value)

        if len(value) > 0:
            value = value[0]

            if value:
                dict[dict_name] = str(value.dt)


def add_attendee_field(component, event):
    attendee = component.get('attendee')
    if attendee:
        if type(attendee) == ListType:
            names = [name[7:] if name.startswith('mailto:') else name for name in attendee]

            event['Attendees'] = unicode(', '.join(names))
        else:
            att = unicode(attendee)

            event['Attendees'] = att[7:] if att.startswith('mailto:') else att


def add_mail_field(component, component_name, dict, dict_name):
    value = component.get(component_name)

    if value:
        name = unicode(value)

        dict[dict_name] = name[7:] if name.startswith('mailto:') else name


def process_calendar(calendar):
    events = []

    for component in calendar.walk():
        if component.name == "VEVENT":
            event = {}

            add_text_field(component, 'summary', event, 'Summary')
            add_text_field(component, 'description', event, 'Description')
            add_mail_field(component, 'organizer', event, 'Organizer')
            add_text_field(component, 'location', event, 'Location')

            add_date_field(component, 'dtstart', event, 'Start')
            add_date_field(component, 'dtend', event, 'End')
            add_date_field(component, 'created', event, 'Created')

            add_attendee_field(component, event)

            events.append(event)

    sorted_events = sorted(events, key=lambda event: event.get('Start'))

    return sorted_events


def log_upload(current_conversion, time):
    new_upload = download_item.Download()

    new_upload.download = False
    new_upload.hash = current_conversion.hash
    new_upload.filename = current_conversion.full_filename
    new_upload.file_size = current_conversion.file_size
    new_upload.time = time

    new_upload.put()


def log_download(current_conversion, time, extension):
    new_download = download_item.Download()

    new_download.download = True
    new_download.hash = current_conversion.hash
    new_download.filename = current_conversion.full_filename
    new_download.file_size = current_conversion.file_size
    new_download.time = time
    new_download.extension = extension

    new_download.put()


def support_email(subject, message):
    mail.send_mail(sender="ICS Convert Support <simon.hutton@gmail.com>",
                   to="Simon <simon.hutton@gmail.com>",
                   subject=subject,
                   body=message)


def format_events_for_html(events):

    for event in events:
        if 'Summary' in event:
            event['Summary'] = event['Summary'].replace('\n', '<br/>')

        if 'Description' in event:
            event['Description'] = event['Description'].replace('\n', '<br/>')

    return events


def format_events_for_txt(events):

    for event in events:
        if 'Summary' in event:
            event['Summary'] = event['Summary'].replace('\n', '\r\n')

        if 'Description' in event:
            event['Description'] = event['Description'].replace('\n', '\r\n')

    return events


def process_aco(file):
    return None


def process_colors(colors):
    return None