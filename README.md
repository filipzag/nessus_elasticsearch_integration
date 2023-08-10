## Nessus reports importer for Elasticsearch

This script pulls scan results from Nessus and indexes data to elasticsearch.

All requirementes are specified in requirementes.txt

### Prerequisites

Following environment variables need to be defined:
  * ACCESS_KEY - nessus access key
  * SECRET_KEY - nessus secret key
  * ES_HOST - elasticsearch host FQDN or IP
  * ES_PORT - elasticsearch port
  * ES_ID - ID for generated elasticsearch API key
  * ES_KEY - elasticsearch API key
  * ES_INDEX - name of index that receives reports
  * ES_DATASTREAM - name of datastream that receives reports(choose either data stream or index)
  * NESSUS_HOST - Nessus host FQDN or IP
  * NESSUS__PORT - Nessus port
  * MAX_AGE - defines how old scan reports to pull each time defined in hours

### Usage


	python3 generate_reports.py

### Docker usage

Build image:

    docker build . -t nessus_reports:latest

Run

	docker run -rm -e ACCESS_KEY=${ACCESS_KEY} -e SECERT_KEY=${SECRET_KEY} -e ES_HOST=${ES_HOST} -e ES_PORT=${ES_PORT} -e ES_ID=${ES_ID} -e ES_KEY=${ES_KEY} -e NESSUS_HOST=${NESSUS_HOST} -e NESSUS_PORT=${NESSUS_PORT} -e MAX_AGE=${MAX_AGE} -e ES_INDEX=${ES_INDEX} nessus_reports:latest


Cron job example	
	0 * * * * docker run --rm -e ACCESS_KEY={} -e SECRET_KEY={} -e ES_HOST={} -e ES_PORT={} -e ES_ID={} -e ES_KEY={} -e NESSUS_HOST={} -e NESSUS_PORT={} -e MAX_AGE=1 -e ES_DATASTREAM={} --network host nessus_reports | logger  2>&1; if [ $? -ne 0 ]; then curl -XPOST https://hooks.slack.com/services/{} -H "Content-Type: application/json" -d "{\"text\": \"Nessus1 reports script failed at dck1\" }" ; fi
