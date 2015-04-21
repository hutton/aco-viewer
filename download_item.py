from google.appengine.ext import ndb

__author__ = 'simonhutton'

# Hash, BlobKey, Created Date, Date Paid, FileName, FileSize

class Download(ndb.Model):
    '''
    classdocs
    '''

    download = ndb.BooleanProperty()
    hash = ndb.StringProperty()
    filename = ndb.StringProperty()
    extension = ndb.StringProperty()
    file_size = ndb.IntegerProperty()
    time = ndb.FloatProperty()
    created_date = ndb.DateTimeProperty(auto_now_add=True)
