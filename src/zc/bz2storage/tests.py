##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
from __future__ import print_function

import unittest
import doctest
import bz2
import binascii
import re
import pickle

import manuel.capture
import manuel.doctest
import manuel.testing
import transaction
import ZEO.tests.testZEO
import ZODB.config
import ZODB.FileStorage
import ZODB.interfaces
import ZODB.MappingStorage
import ZODB.tests.StorageTestBase
import ZODB.tests.testFileStorage
import ZODB.utils
import zope.interface.verify
from zope.testing import setupstack
from zope.testing.renormalizing import RENormalizing

import zc.bz2storage

def _copy(dest, src):
    with open(src, 'rb') as srcf:
        with open(dest, 'wb') as destf:
            destf.write(srcf.read())

def test_config():
    r"""

To configure a bz2storage, import zc.bz2storage and use the
bz2storage tag:

    >>> config = '''
    ...     %import zc.bz2storage
    ...     <zodb>
    ...         <bz2storage>
    ...             <filestorage>
    ...                 path data.fs
    ...                 blob-dir blobs
    ...             </filestorage>
    ...         </bz2storage>
    ...     </zodb>
    ... '''
    >>> db = ZODB.config.databaseFromString(config)

    >>> conn = db.open()
    >>> conn.root()['a'] = 1
    >>> transaction.commit()
    >>> conn.root()['b'] = ZODB.blob.Blob(b'Hi\nworld.\n')
    >>> transaction.commit()

    >>> db.close()

    >>> db = ZODB.config.databaseFromString(config)
    >>> conn = db.open()
    >>> conn.root()['a']
    1
    >>> conn.root()['b'].open().read() == b'Hi\nworld.\n'
    True
    >>> db.close()

After putting some data in, the records will be compressed, unless
doing so would make them bigger:

    >>> for t in ZODB.FileStorage.FileIterator('data.fs'):
    ...     for r in t:
    ...         data = r.data
    ...         if r.data[:2] != b'.z':
    ...             if len(bz2.compress(data))+2 < len(data):
    ...                 print('oops', repr(r.oid))
    ...         else: _ = bz2.decompress(data[2:])
    """

def test_config_no_compress():
    r"""

You can disable compression.

    >>> config = '''
    ...     %import zc.bz2storage
    ...     <zodb>
    ...         <bz2storage>
    ...             compress no
    ...             <filestorage>
    ...                 path data.fs
    ...                 blob-dir blobs
    ...             </filestorage>
    ...         </bz2storage>
    ...     </zodb>
    ... '''
    >>> db = ZODB.config.databaseFromString(config)

    >>> conn = db.open()
    >>> conn.root()['a'] = 1
    >>> transaction.commit()
    >>> conn.root()['b'] = ZODB.blob.Blob(b'Hi\nworld.\n')
    >>> transaction.commit()

    >>> db.close()

Since we didn't compress, we can open the storage using a plain file storage:

    >>> db = ZODB.DB(ZODB.FileStorage.FileStorage('data.fs', blob_dir='blobs'))
    >>> conn = db.open()
    >>> conn.root()['a']
    1
    >>> conn.root()['b'].open().read() == b'Hi\nworld.\n'
    True
    >>> db.close()
    """

def test_mixed_compressed_and_uncompressed_and_packing():
    r"""
We can deal with a mixture of compressed and uncompressed data.

First, we'll create an existing file storage:

    >>> db = ZODB.DB(ZODB.FileStorage.FileStorage('data.fs', blob_dir='blobs'))
    >>> conn = db.open()
    >>> conn.root.a = 1
    >>> transaction.commit()
    >>> conn.root.b = ZODB.blob.Blob(b'Hi\nworld.\n')
    >>> transaction.commit()
    >>> conn.root.c = conn.root().__class__((i,i) for i in range(100))
    >>> transaction.commit()
    >>> db.close()

Now let's open the database compressed:

    >>> db = ZODB.DB(zc.bz2storage.Bz2Storage(
    ...     ZODB.FileStorage.FileStorage('data.fs', blob_dir='blobs')))
    >>> conn = db.open()
    >>> conn.root()['a']
    1
    >>> conn.root()['b'].open().read() == b'Hi\nworld.\n'
    True
    >>> conn.root()['b'] = ZODB.blob.Blob(b'Hello\nworld.\n')
    >>> transaction.commit()
    >>> db.close()

Having updated the root, it is now compressed.  To see this, we'll
open it as a file storage and inspect the record for object 0:

    >>> storage = ZODB.FileStorage.FileStorage('data.fs')
    >>> data, _ = storage.load(b'\0'*8)
    >>> data[:2] == b'.z'
    True
    >>> pickle.loads(bz2.decompress(data[2:]))
    <class 'persistent.mapping.PersistentMapping'>

The new blob record is uncompressed because it is too small:

    >>> data, _ = storage.load(b'\0'*7+b'\3')
    >>> data[:2] == b'.z'
    False
    >>> pickle.loads(data)
    <class 'ZODB.blob.Blob'>

Records that we didn't modify remain uncompressed

    >>> data, _ = storage.load(b'\0'*7+b'\2')
    >>> data[:2] == b'.z'
    False
    >>> pickle.loads(data)
    <class 'persistent.mapping.PersistentMapping'>

    >>> storage.close()

Let's try packing the file 4 ways:

- using the compressed storage:

    >>> _copy('data.fs.save', 'data.fs')
    >>> db = ZODB.DB(zc.bz2storage.Bz2Storage(
    ...     ZODB.FileStorage.FileStorage('data.fs', blob_dir='blobs')))
    >>> db.pack()
    >>> sorted(ZODB.utils.u64(i[0]) for i in record_iter(db.storage))
    [0, 2, 3]
    >>> db.close()

- using the storage in non-compress mode:

    >>> _copy('data.fs', 'data.fs.save')
    >>> db = ZODB.DB(zc.bz2storage.Bz2Storage(
    ...     ZODB.FileStorage.FileStorage('data.fs', blob_dir='blobs'),
    ...     compress=False))

    >>> db.pack()
    >>> sorted(ZODB.utils.u64(i[0]) for i in record_iter(db.storage))
    [0, 2, 3]
    >>> db.close()
    """

class Dummy:

    def invalidateCache(self):
        print('invalidateCache called')

    def invalidate(self, *args):
        print('invalidate', args)

    def references(self, record, oids=None):
        if oids is None:
            oids = []
        oids.extend(binascii.unhexlify(record).split())
        return oids

    def transform_record_data(self, data):
        return binascii.hexlify(data)

    def untransform_record_data(self, data):
        return binascii.unhexlify(data)


def test_wrapping():
    """
Make sure the wrapping methods do what's expected.

    >>> s = zc.bz2storage.Bz2Storage(ZODB.MappingStorage.MappingStorage())
    >>> zope.interface.verify.verifyObject(ZODB.interfaces.IStorageWrapper, s)
    True

    >>> s.registerDB(Dummy())
    >>> s.invalidateCache()
    invalidateCache called

    >>> s.invalidate('1', list(range(3)), '')
    invalidate ('1', [0, 1, 2])

    >>> data = b'0 1 2 3 4 5 6 7 8'
    >>> transformed = s.transform_record_data(data)
    >>> transformed == b'.z'+bz2.compress(binascii.hexlify(data))
    True

    >>> s.untransform_record_data(transformed) == data
    True

    >>> s.references(transformed)
    ['0', '1', '2', '3', '4', '5', '6', '7', '8']

    >>> l = list(range(3))
    >>> s.references(transformed, l)
    [0, 1, 2, '0', '1', '2', '3', '4', '5', '6', '7', '8']

    >>> l
    [0, 1, 2, '0', '1', '2', '3', '4', '5', '6', '7', '8']

If the data are small or otherwise not compressable, it is left as is:

    >>> data = b'0 1'
    >>> transformed = s.transform_record_data(data)
    >>> transformed == b'.z'+bz2.compress(binascii.hexlify(data))
    False

    >>> transformed == binascii.hexlify(data)
    True

    >>> s.untransform_record_data(transformed) == data
    True

    >>> s.references(transformed)
    ['0', '1']

    >>> l = list(range(3))
    >>> s.references(transformed, l)
    [0, 1, 2, '0', '1']

    >>> l
    [0, 1, 2, '0', '1']
    """

def dont_double_compress():
    """
    This test is a bit artificial in that we want to make sure we
    don't double compress and we don't want to rely on not double
    compressing simply because doing so would make the pickle smaller.
    So this test is actually testing that we don't compress strings
    that start withe the compressed marker.

    >>> data = b'.z'+b'x'*80
    >>> store = zc.bz2storage.Bz2Storage(ZODB.MappingStorage.MappingStorage())
    >>> store._transform(data) == data
    True
    """

def record_iter(store):
    next = None
    while 1:
        oid, tid, data, next = store.record_iternext(next)
        yield oid, tid, data
        if next is None:
            break


class FileStorageBz2Tests(ZODB.tests.testFileStorage.FileStorageTests):

    def open(self, **kwargs):
        self._storage = zc.bz2storage.Bz2Storage(
            ZODB.FileStorage.FileStorage('FileStorageTests.fs',**kwargs))

class FileStorageBz2TestsWithBlobsEnabled(
    ZODB.tests.testFileStorage.FileStorageTests):

    def open(self, **kwargs):
        if 'blob_dir' not in kwargs:
            kwargs = kwargs.copy()
            kwargs['blob_dir'] = 'blobs'
        ZODB.tests.testFileStorage.FileStorageTests.open(self, **kwargs)
        self._storage = zc.bz2storage.Bz2Storage(self._storage)

class FileStorageBz2RecoveryTest(
    ZODB.tests.testFileStorage.FileStorageRecoveryTest):

    def setUp(self):
        ZODB.tests.StorageTestBase.StorageTestBase.setUp(self)
        self._storage = zc.bz2storage.Bz2Storage(
            ZODB.FileStorage.FileStorage("Source.fs", create=True))
        self._dst = zc.bz2storage.Bz2Storage(
            ZODB.FileStorage.FileStorage("Dest.fs", create=True))



class FileStorageZEOBz2Tests(ZEO.tests.testZEO.FileStorageTests):
    _expected_interfaces = (
        ('ZODB.interfaces', 'IStorageRestoreable'),
        ('ZODB.interfaces', 'IStorageIteration'),
        ('ZODB.interfaces', 'IStorageUndoable'),
        ('ZODB.interfaces', 'IStorageCurrentRecordIteration'),
        ('ZODB.interfaces', 'IExternalGC'),
        ('ZODB.interfaces', 'IStorage'),
        ('ZODB.interfaces', 'IStorageWrapper'),
        ('zope.interface', 'Interface'),
        )

    def getConfig(self):
        return """\
        %import zc.bz2storage
        <bz2storage>
        <filestorage 1>
        path Data.fs
        </filestorage>
        </bz2storage>
        """

class FileStorageClientBz2ZEOBz2Tests(FileStorageZEOBz2Tests):

    def _wrap_client(self, client):
        return zc.bz2storage.Bz2Storage(client)

class FileStorageClientBz2ZEOServerBz2Tests(
    FileStorageClientBz2ZEOBz2Tests
    ):

    def getConfig(self):
        return """\
        %import zc.bz2storage
        <serverbz2storage>
        <filestorage 1>
        path Data.fs
        </filestorage>
        </serverbz2storage>
        """

class TestIterator(unittest.TestCase):

    def test_iterator_closes_underlying_explicitly(self):
        # https://github.com/zopefoundation/zc.bz2storage/issues/4

        class Storage(object):

            storage_value = 42
            iterator_closed = False

            def registerDB(self, db):
                pass

            def iterator(self, start=None, stop=None):
                return self

            def __iter__(self):
                return self

            def __next__(self):
                return self

            next = __next__

            def close(self):
                self.iterator_closed = True

        storage = Storage()
        zstorage = zc.bz2storage.Bz2Storage(storage)

        it = zstorage.iterator()

        # Make sure it proxies all attributes
        self.assertEqual(42, getattr(it, 'storage_value'))

        # Make sure it iterates (whose objects also proxy)
        self.assertEqual(42, getattr(next(it), 'storage_value'))

        # The real iterator is closed
        it.close()

        self.assertTrue(storage.iterator_closed)

        # And we can't move on; the wrapper prevents it even though
        # the underlying storage implementation is broken
        self.assertRaises(StopIteration, next, it)

        # We can keep closing it though
        it.close()

class TestServerBz2Storage(unittest.TestCase):

    def test_load_doesnt_decompress(self):
        # ServerBz2Storage.load doesn't uncompress the record.
        # (This prevents it from being used with a ZODB 5 Connection)
        # See https://github.com/zopefoundation/zc.bz2storage/issues/5
        map_store = ZODB.MappingStorage.MappingStorage()
        store = zc.bz2storage.Bz2Storage(map_store)
        # Wrap a database to create the root object, and add data to make it
        # big enough to compress
        db = ZODB.DB(store)
        conn = db.open()
        conn.root.a = b'x' * 128
        transaction.commit()
        conn.close()

        root_data, _ = store.load(ZODB.utils.z64)
        self.assertNotEqual(root_data[:2], b'.z')

        server_store = zc.bz2storage.ServerBz2Storage(map_store)
        server_root_data, _ = server_store.load(ZODB.utils.z64)
        self.assertEqual(server_root_data[:2], b'.z')

        db.close()


def test_suite():
    suite = unittest.TestSuite()
    for class_ in (
        FileStorageBz2Tests,
        FileStorageBz2TestsWithBlobsEnabled,
        FileStorageBz2RecoveryTest,
        FileStorageZEOBz2Tests,
        FileStorageClientBz2ZEOBz2Tests,
        FileStorageClientBz2ZEOServerBz2Tests,
        ):
        s = unittest.makeSuite(class_, "check")
        s.layer = ZODB.tests.util.MininalTestLayer(
            'bz2storagetests.%s' % class_.__name__)
        suite.addTest(s)

    suite.addTest(unittest.makeSuite(TestIterator))
    suite.addTest(unittest.makeSuite(TestServerBz2Storage))

    # The conflict resolution and blob tests don't exercise proper
    # plumbing for bz2storage because the sample data they use
    # compresses to larger than the original.  Run the tests again
    # after monkey patching bz2storage to compress everything.

    class Bz2HackLayer:

        orig = [zc.bz2storage.compress] # []s hide the function :)

        @classmethod
        def setUp(self):
            zc.bz2storage.transform = (
                lambda data: data and (b'.z'+bz2.compress(data)) or data
                )

        @classmethod
        def tearDown(self):
            [zc.bz2storage.compress] = self.orig

    s = unittest.makeSuite(FileStorageBz2TestsWithBlobsEnabled, "check")
    s.layer = Bz2HackLayer
    suite.addTest(s)

    checker = RENormalizing([
        # Py3k renders bytes where Python2 used native strings...
        (re.compile(r"b'"), "'"),
        (re.compile(r'b"'), '"'),
        # Older versions of PyPy2 (observed in PyPy2 5.4 but not 5.6)
        # produce long integers (1L) where we expect normal ints
        (re.compile(r"(\d)L"), r"\1")
    ])

    suite.addTest(doctest.DocTestSuite(
        checker=checker,
        setUp=setupstack.setUpDirectory, tearDown=setupstack.tearDown
        ))
    suite.addTest(manuel.testing.TestSuite(
        manuel.doctest.Manuel() + manuel.capture.Manuel(),
        'README.txt',
        setUp=setupstack.setUpDirectory, tearDown=setupstack.tearDown
        ))
    return suite
