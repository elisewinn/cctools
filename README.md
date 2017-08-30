# cctools
Iterate over WARC files that are cached locally

## Installation

```
pip install -r requirements.txt
```

You need have an Amazon AWS account with keys for S3. After
`boto3` has been installed, you must configure it to use
your AWS credentials. See the [boto3 documentation](http://boto3.readthedocs.io/en/latest/guide/quickstart.html) for details.

## Use

```
python3 cctools.py 2017-34 www.celebuzz.com/2017-01-04/*
```

Will iterate over WARC files in the `2017-34` Common Crawl
archive with URL's matching `www.celebuzz.com/2017-01-04/*`. Results
are instances of class `ArcWarcRecord` from the [warcio](https://github.com/webrecorder/warcio/) 
package. See `cctools.py` for further details and an example. 

## Internals

The `WARCManager.iterate_warcs` method first retrieves a list of 
WARCs matching the search criteria. These results are cached to
disk. It then iterates over this list and returns WARC files. If these
WARC files are found in the local cache, the local copies are returned.
Otherwise they are downloaded from S3 and cached locally.