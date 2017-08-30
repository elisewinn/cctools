#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 28 16:04:18 2017

@author: Jason M.T. Roos
"""

import argparse
from WARCManager import WARCManager, Config
import logging


def main():
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    
    ap = argparse.ArgumentParser('CC Tools')
    ap.add_argument('index', help = 'CC index in yyyy-ww format')
    ap.add_argument('url', help = 'URL to query')

    ap.add_argument('-s', '--search-results-location', required = False, 
                    help = 'Directory to store cached CC index server calls', 
                    default = './search-results/')
    ap.add_argument('-w', '--warc-location', required = False,
                    help = 'Directory to store root of cached WARC archives',
                    default = './')

    args = None
    try:
        args = vars(ap.parse_args())
    except:
        pass
        # Print out the default help text and exit
    
        
    if(args):
        url = args['url']
        index = args['index']
        
        # determines where warc index search results and gzipped warc files
        # are cached. By default, in './search-results/' and './' in the
        # local execution directory.
        config = Config(search_results_dir = args['search_results_location'],
                                          cc_cache_dir = args['warc_location'])
        
        # create an instance of the WARCManager class
        warcs = WARCManager(config) 
        
        # the index server is called without a filter. After search results are 
        # retrieved, we will only iterate through warcs whose index server
        # search result match this criteria.
        index_filter = lambda x: (x.status == '200' and 
                                  x.mime == "text/html")

        # here is an example of what you can do with the 
        # WARCManager.iterate_warcs method
        for warc in warcs.iterate_warcs(url, index, index_filter):
            # after pip3 install newspaper...
            print('\n' + warc.rec_headers.get_header('WARC-Target-URI'))
            # article = newspaper.Article(warc.rec_headers.get_header('WARC-Target-URI'))
            # html = warc.raw_stream.read()
            # if html != b'':
                # article.download(input_html = html)
                # article.parse()
                # print(article.title)
            
            


if __name__ == "__main__":
    main()






