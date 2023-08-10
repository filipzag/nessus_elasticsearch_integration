from tenable.nessus import Nessus
from tenable.base.platform import APIPlatform
import json
import csv
from elasticsearch import AsyncElasticsearch 
import urllib3
import warnings
from datetime import datetime, timedelta
import socket
import os
import asyncio
from elasticsearch.helpers import async_bulk
from itertools import tee


#urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.simplefilter(action='ignore', category=Warning)


access_key = os.getenv('ACCESS_KEY')
secret_key = os.getenv('SECRET_KEY')
es_host = os.getenv('ES_HOST')
es_port = os.getenv('ES_PORT')
es_id = os.getenv('ES_ID')
es_key = os.getenv('ES_KEY')
es_index = os.getenv('ES_INDEX')
es_datastream = os.getenv('ES_DATASTREAM') 
nessus_host = os.getenv('NESSUS_HOST')
nessus_port = os.getenv('NESSUS_PORT')
max_age = os.getenv('MAX_AGE')



class NotDefinedException(Exception):

    def __init__(self, message="Needed environment variable is not defined!"):
        self.message = message
        super().__init__(self.message)


def determine_output(es_index, es_datastream):


    if es_index != None:
        action = "index"
    elif es_datastream != None:
        action = "create"


    if action == None:
        raise NotDefinedException
    elif action == "index":
        output = es_index
    else:
        output = es_datastream

    return action, output


def check_connections():

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.settimeout(5)
            s.connect((es_host, int(es_port)))
            s.close()
        except Exception as e_es:
            print(f'Can not connect to elasticsearch server: {e_es}')
            exit(1)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:      
        try:
            s.settimeout(5)
            s.connect((nessus_host, int(nessus_port)))
            s.close()
        except Exception as e_ns:
            print(f'Can not connect to Nessus server: {e_ns}')
            exit(1)


async def elasticsearch_bulk_index(docs):
    
    es = AsyncElasticsearch(
        'https://' + es_host + ':' + es_port,
        api_key=(es_id, es_key),
        verify_certs=False )
    docs_gen, doc_helper = tee(docs)
    bulk_list = []

    next(doc_helper)
    for doc in docs_gen:
        if len(bulk_list) == 100:
            await async_bulk(es, actions=bulk_list)
            bulk_list = []

        else:
            bulk_list.append(doc)

        try:
            next(doc_helper)
        except StopIteration:
            await async_bulk(es, actions=bulk_list)

def get_latest_scans(lookback_time):

    # Lookbacktime in hours
    global ns    

    ns = Nessus(url='https://' + nessus_host + ':' + nessus_port)
    ns._key_auth(access_key, secret_key)

    wanted_time = datetime.now() - timedelta(hours=int(lookback_time))
    wanted_time = int(wanted_time.replace(microsecond=0).timestamp())
    all_scans = ns.scans.list(last_modification_date=wanted_time)

    if isinstance(all_scans['scans'], list):

        return all_scans['scans']
    else: return []


def get_es_doc(row, scan_name, timestamp):

    elasticsearch_doc = {}
     
    for key in row.keys():            
        
        clean_key = key.lower().replace(' ', '_').replace('.','_')        
        elasticsearch_doc[clean_key] = row[key]        
        elasticsearch_doc['scan_name'] = scan_name
        elasticsearch_doc['_index'] = output
        elasticsearch_doc['_op_type'] = action
        elasticsearch_doc['@timestamp'] = timestamp
        
    return elasticsearch_doc

def import_scans(scans):

    for scan in scans:

        print(f'Nessus report import - Scan name: {scan["name"]}, scan ID {scan["id"]}')
        scan_data_gen = (row for row in ns.scans.export_scan(scan['id'], format = 'csv' ).getvalue().decode('utf-8').split('\n'))

        csv_data = csv.DictReader(scan_data_gen)


        es_docs = ( get_es_doc(row, scan['name'], scan['last_modification_date'] ) for row in csv_data  )


        loop = asyncio.get_event_loop()
        loop.run_until_complete(elasticsearch_bulk_index(es_docs))

check_connections()

action, output = determine_output(es_index, es_datastream)

import_scans(get_latest_scans(max_age))

