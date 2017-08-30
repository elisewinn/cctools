#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 28 16:04:18 2017

@author: Jason M.T. Roos
"""

import hashlib
import logging
import boto3
import os
import warcio
import json
import cdx_query
from dotmap import DotMap

class Config:
    
    def __init__(self, 
                 search_results_dir = './search-results',
                 cc_cache_dir = './'):
        if search_results_dir:
            self.search_results_dir = search_results_dir
        if cc_cache_dir:
            self.cc_cache_dir = cc_cache_dir
        
        
        
class WARCManager:
    
    
    def __init__(self, config = Config()):
        self.config = config
        self.s3 = None

    
    def search_results_fn(self, fn):
        return self.config.search_results_dir + fn
    
    def cc_cache_fn(self, fn, start, end):
        warc_fn, gz = os.path.splitext(fn)
        raw_file, warc = os.path.splitext(warc_fn)
        return self.config.cc_cache_dir + raw_file + '-{}-{}'.format(start, end) + warc + gz
    
    def ensure_dir(self, fn):
        dir = os.path.dirname(fn)
        if not os.path.exists(dir):
            os.makedirs(dir)
    
    def get_cc_index_server_files(self, url, index):    
        cdx_server_url = "http://index.commoncrawl.org/CC-MAIN-{}-index".format(index)
        index_key = '{}?url={}'.format(cdx_server_url, url)
        m = hashlib.blake2b(digest_size=10)
        m.update(index_key.encode('UTF-8'))
        index_key_digest = m.hexdigest()
        
        self.ensure_dir(self.config.search_results_dir)
        results_cached = any(x.startswith(index_key_digest) for x in os.listdir(self.config.search_results_dir))
        
        if not results_cached:
            logging.info('Searching CC index and caching results.' )
            
            r = DotMap()
            r.coll = index
            r.url = url
            r.json = True
            r.timeout = 30
            r.max_retries = 5
            r.show_num_pages = False
            r.cdx_server_url = cdx_server_url
            r.output_prefix = self.search_results_fn(index_key_digest + '-')
            
            cdx_query.read_index(r)
    
        return list(filter(lambda x: x.startswith(index_key_digest), 
                           os.listdir(self.search_results_fn(''))))
    
    def iterate_cc_index_server_results(self, url, index, fl = None):
        # default filter: return all results
        fl_ = lambda x: True
        if fl is not None:
            fl_ = fl
            
        for page in self.get_cc_index_server_files(url, index):
            with open(self.search_results_fn(page), 'r') as f:
                for line in f.readlines():
                    j = DotMap(json.loads(line))
                    # apply filter
                    if fl_(j):
                        yield(j)
                
    
    def get_warc(self, cc_filename, start, end):
        fn = self.cc_cache_fn(cc_filename, start, end)
        if not os.path.isfile(fn):
            try:
                logging.info('Downloading CC file segment from S3')
                segment = self.s3.get_object(Bucket = "commoncrawl", Key = cc_filename, 
                                        Range = 'bytes={}-{}'.format(start, end))
                self.ensure_dir(fn)
                with open(fn, 'wb+') as f:
                    f.write(segment['Body'].read())
                return [fn]
            except:
                logging.error('Unable to download CC file segment from S3')
                return ['']
        else:
            return [fn]
    
    def iterate_warcs(self, url, index, index_filter):
        if self.s3 is None:
            self.s3 = boto3.client('s3')
        for search_result in self.iterate_cc_index_server_results(url, index, index_filter):
            start = int(search_result['offset'])
            end = start + int(search_result['length']) - 1
            cc_filename = search_result['filename']        
            for warc_fn in self.get_warc(cc_filename, start, end):
                with open(warc_fn, 'rb') as f:
                    for warc in warcio.ArchiveIterator(f):
                        yield(warc)