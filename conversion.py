import sys
sys.path.insert(0, 'libs')

from google.appengine.ext import ndb

from google.appengine.ext import blobstore

from helper import process_aco, process_colors

__author__ = 'simonhutton'

# Hash, BlobKey, Created Date, Date Paid, FileName, FileSize

class Conversion(ndb.Model):
    '''
    classdocs
    '''

    hash = ndb.StringProperty()
    blob_key = ndb.BlobProperty()
    created_date = ndb.DateTimeProperty(auto_now_add=True)
    filename = ndb.StringProperty()
    file_size = ndb.IntegerProperty()
    full_filename = ndb.StringProperty()
    color_count = ndb.IntegerProperty()
    todo_count = ndb.IntegerProperty()

    def get_palette(self):
        blob_reader = blobstore.BlobReader(self.blob_key)

        file_content = blob_reader.read()

        raw_colors = process_aco(file_content)

        return process_colors(raw_colors)
