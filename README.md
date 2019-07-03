# ZODB storage wrapper for bz2 compression of database records

## Introduction

The ``bc.bz2storage`` package provides ZODB storage wrapper
implementations that provides compression of database records.

Bz2 version gives significant improvement of the compression.
Originally, tested on JSON format 368kb string which resulted:
103kb zc.zlibstorage
78kb bc.bz2storage

## Table of contens
* [Installation](#installation)
* [Usage](#usage)
* [Credits](#credits)

### Installation

    pip install bc.bz2sotrage
    pip install git+https://github.com/qpaycm/bc/bz2storage
    
### Usage
    
    from ZODB import FileStorage, DB

    import bz2
    import bz2storage
    import transaction

    #	create storage
    storage = bz2storage.Bz2Storage(FileStorage.FileStorage('data.fs'))
    #	create DB that uses our storage
    db = DB(storage)
    #	open DB connection object
    connection = db.open()
    #	get the root access
    root = connection.root()

    #	Now you can use root.items() to list DB
    for doc in root.items():
        print(doc)

### Credits

* Major revision ideas taken from jimfulton's python library

  - https://github.com/zopefoundation/zc.zlibstorage/

See src/bc/bz2storage/README.txt.