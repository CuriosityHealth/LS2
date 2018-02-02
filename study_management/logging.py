import logging
import logging.handlers
import zipfile
import sys, os, time, glob
import gzip

class TimedCompressedRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):

    def _namer(self, name):
        return name + ".gz"

    def _rotator(self, source, dest):
        with open(source, "rb") as sf:
            data = sf.read()
            with gzip.open(dest, 'wb') as df:
                df.write(data)
        os.remove(source)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.namer = self._namer
        self.rotator = self._rotator
