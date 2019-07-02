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
* [Credits](#credits)

### Installation

    pip install git+https://github.com/qpaycm/bc/bz2storage
    
### Credits

* Major revision ideas taken from jimfulton's python library

  - https://github.com/zopefoundation/zc.zlibstorage/

See src/bc/bz2storage/README.txt.
