import os
import json
import hashlib

META_PREFIX = os.path.join('meta', '')
DATA_PREFIX = os.path.join('data', '')
HASH_FUNC = hashlib.sha256
HASH_SIZE = len(HASH_FUNC().hexdigest())


class MetaFolder(object):

    def __init__(self, path):
        self.path = path

    def close(self):
        pass

    def get(self, identifier):
        return MetaItem(self, identifier=identifier)

    def add_file(self, source_path, identifier=None, meta=None):
        identifier = identifier or source_path
        meta = meta or {}
        if 'source_path' not in meta:
            meta['source_path'] = source_path
        item = MetaItem(self, identifier=identifier)
        item.meta = meta
        return item

    @property
    def _meta_base(self):
        return os.path.join(self.path, META_PREFIX)

    @property
    def _data_base(self):
        return os.path.join(self.path, DATA_PREFIX)

    def __iter__(self):
        for (dirname, _, files) in os.walk(self._data_base):
            for file_name in files:
                if len(file_name) == HASH_SIZE:
                    yield MetaItem(self, hash_=file_name)

    def __enter__(self):
        return self

    def __exit__(self):
        self.close()

    def __unicode__(self):
        return self.path

    def __repr__(self):
        return '<Metafolder(%r)>' % self.path


class MetaItem(object):

    def __init__(self, folder, identifier=None, hash_=None, meta=None):
        self.folder = folder
        self._identifier = identifier
        self._hash = hash_
        self._meta = meta

    @property
    def hash(self):
        if self._hash is None and self._identifier is not None:
            self._hash = self.get_hash(self._identifier)
        if self._hash is None:
            raise ValueError("No hash for MetaItem!")
        return self._hash

    @property
    def identifier(self):
        if self._identifier is None:
            self._identifier = self.meta.get('$identifier')
        return self._identifier

    @property
    def _data_path(self):
        return os.path.join(self.folder._data_base, self.hash[:2],
                            self.hash[2:4], self.hash[4:6], self.hash)

    @property
    def _meta_path(self):
        fn = '%s.json' % self.hash
        return os.path.join(self.folder._data_base, self.hash[:2],
                            self.hash[2:4], self.hash[4:6], fn)

    @property
    def meta(self):
        if self._meta is None:
            try:
                with open(self._meta_path, 'r') as fh:
                    self._meta = json.load(fh)
            except KeyError:
                self._meta = {'$identifier': self._identifier}
        return self._meta

    @meta.setter
    def meta(self, value):
        if self._identifier is not None:
            value['$identifier'] = self._identifier
        self._meta = value
        try:
            os.makedirs(os.path.dirname(self._meta_path))
        except:
            pass
        with open(self._meta_path, 'w') as fh:
            json.dump(self._meta, fh)

    def __unicode__(self):
        return self.identifier

    def __repr__(self):
        return '<MetaItem(%r, %r)>' % (self.identifier, self.hash)

    @classmethod
    def get_hash(cls, identifier):
        return hashlib.sha256(identifier).hexdigest()