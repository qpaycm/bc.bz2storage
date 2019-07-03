=============================================================
ZODB storage wrapper for bz2 compression of database records
=============================================================

The ``zc.bz2storage`` package provides ZODB storage wrapper
implementations that provides compression of database records.

.. contents::

Usage
=====

The primary storage is ``zc.bz2storage.Bz2Storage``.  It is used as
a wrapper around a lower-level storage.  From Python, it is
constructed by passing another storage, as in::

    import ZODB.FileStorage, zc.bz2storage

    storage = zc.bz2storage.Bz2Storage(
        ZODB.FileStorage.FileStorage('data.fs'))

.. -> src

    >>> import bz2
    >>> exec(src)
    >>> data = b'x'*100
    >>> storage.transform_record_data(data) == b'.z'+bz2.compress(data)
    True
    >>> storage.close()

When using a ZODB configuration file, the bz2storage tag is used::

    %import zc.bz2storage

    <zodb>
      <bz2storage>
        <filestorage>
          path data.fs
        </filestorage>
      </bz2storage>
    </zodb>

.. -> src

    >>> import ZODB.config
    >>> db = ZODB.config.databaseFromString(src)
    >>> db.storage.transform_record_data(data) == b'.z'+bz2.compress(data)
    True
    >>> db.close()

Note the ``%import`` used to load the definition of the
``bz2storage`` tag.

Use with ZEO
============

When used with a ZEO ClientStorage, you'll need to use a server bz2
storage on the storage server.  This is necessary so that server
operations that need to get at uncompressed record data can do so.
This is accomplished using the ``serverbz2storage`` tag in your ZEO
server configuration file::

    %import zc.bz2storage

    <zeo>
      address 8100
    </zeo>

    <serverbz2storage>
      <filestorage>
        path data.fs
      </filestorage>
    </serverbz2storage>

.. -> src

    >>> src = src[:src.find('<zeo>')]+src[src.find('</zeo>')+7:]

    >>> storage = ZODB.config.storageFromString(src)
    >>> storage.transform_record_data(data) == b'.z'+bz2.compress(data)
    True
    >>> storage.__class__.__name__
    'ServerBz2Storage'

    >>> storage.close()

Applying compression on the client this way is attractive because, in
addition to reducing the size of stored database records on the
server, you also reduce the size of records sent from the server to the
client and the size of records stored in the client's ZEO cache.

Decompressing only
==================

By default, records are compressed when written to the storage and
uncompressed when read from the storage.  A ``compress`` option can be
used to disable compression of records but still uncompress compressed
records if they are encountered. Here's an example from in Python::

    import ZODB.FileStorage, zc.bz2storage

    storage = zc.bz2storage.Bz2Storage(
        ZODB.FileStorage.FileStorage('data.fs'),
        compress=False)

.. -> src

    >>> exec(src)
    >>> storage.transform_record_data(data) == data
    True
    >>> storage.close()

and using the configurationb syntax::

    %import zc.bz2storage

    <zodb>
      <bz2storage>
        compress false
        <filestorage>
          path data.fs
        </filestorage>
      </bz2storage>
    </zodb>

.. -> src

    >>> db = ZODB.config.databaseFromString(src)
    >>> db.storage.transform_record_data(data) == data
    True
    >>> db.close()

This option is useful when deploying the storage when there are
multiple clients.  If you don't want to update all of the clients at
once, you can gradually update all of the clients with a bz2 storage
that doesn't do compression, but recognizes compressed records.  Then,
in a second phase, you can update the clients to compress records, at
which point, all of the clients will be able to read the compressed
records produced.

Compressing entire databases
============================

One way to compress all of the records in a database is to copy data
from an uncompressed database to a compressed one, as in::

    import ZODB.FileStorage, zc.bz2storage

    orig = ZODB.FileStorage.FileStorage('data.fs')
    new = zc.bz2storage.Bz2Storage(
        ZODB.FileStorage.FileStorage('data.fs-copy'))
    new.copyTransactionsFrom(orig)

    orig.close()
    new.close()

.. -> src

    >>> conn = ZODB.connection('data.fs', create=True)
    >>> conn.root.a = conn.root().__class__([(i,i) for i in range(1000)])
    >>> conn.root.b = conn.root().__class__([(i,i) for i in range(2000)])
    >>> import transaction
    >>> transaction.commit()
    >>> conn.close()

    >>> exec(src)

    >>> new = zc.bz2storage.Bz2Storage(
    ...     ZODB.FileStorage.FileStorage('data.fs-copy'))
    >>> conn = ZODB.connection(new)
    >>> dict(conn.root.a) == dict([(i,i) for i in range(1000)])
    True
    >>> dict(conn.root.b) == dict([(i,i) for i in range(2000)])
    True

    >>> import ZODB.utils
    >>> for i in range(3):
    ...     if not new.base.load(ZODB.utils.p64(i))[0][:2] == b'.z':
    ...         print('oops {}'.format(i))
    >>> len(new)
    3

    >>> conn.close()

Record prefix
=============

Compressed records have a prefix of ".z".  This allows a database to
have a mix of compressed and uncompressed records.

Stand-alone Compression and decompression functions
===================================================

In anticipation of wanting to plug the compression and decompression
logic into other tools without creating storages, the functions used
to compress and uncompress data records are available as
``zc.bz2storage`` module-level functions:

``compress(data)``
   Compress the given data if:

   - it is a string more than 20 characters in length,
   - it doesn't start with the compressed-record marker, ``b'.z'``, and
   - the compressed size is less the original.

   The compressed (or original) data are returned.

``decompress(data)``
   Decompress the data if it is compressed.

   The decompressed (or original) data are returned.

.. basic sanity check :)

   >>> _ = (zc.bz2storage.compress, zc.bz2storage.decompress)

