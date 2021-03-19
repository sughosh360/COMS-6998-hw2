
import json
import boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection
import requests

ES_ENDPOINT = "https://search-photosearchmedium-uhg2nwrxtzwzlxb5fj4tueldom.us-east-1.es.amazonaws.com"
ES_INDEX = "photos"

def detect_labels(photo, bucket):

    client=boto3.client('rekognition')

    response = client.detect_labels( Image = { 'S3Object': {'Bucket':bucket,'Name':photo} } )

    print('Detected labels for ' + photo)
    print()  
    labels = list()
    for label in response['Labels']:
        print ("Label: " + label['Name'])
        print ("Confidence: " + str(label['Confidence']))
       
        # print ("Instances:")
        # for instance in label['Instances']:
        #     print ("  Bounding box")
        #     print ("    Top: " + str(instance['BoundingBox']['Top']))
        #     print ("    Left: " + str(instance['BoundingBox']['Left']))
        #     print ("    Width: " +  str(instance['BoundingBox']['Width']))
        #     print ("    Height: " +  str(instance['BoundingBox']['Height']))
        #     print ("  Confidence: " + str(instance['Confidence']))
        #     print()

        # print ("Parents:")
        # for parent in label['Parents']:
        #     print ("   " + parent['Name'])
        # print ("----------")
        # print ()
       
        labels.append(label['Name'])
       
    return labels

def get_obj_metadata( bucket, key ):
   
    client = boto3.client('s3')
    obj_head = client.head_object( Bucket=bucket, Key=key )
    print( 'ObjHead: {0}'.format(obj_head) )
    meta_data = obj_head['ResponseMetadata']
    if 'x-amz-meta-customlabels' in meta_data['HTTPHeaders'].keys():
        customLabels = meta_data['HTTPHeaders']['x-amz-meta-customlabels'].split(", ")
    else:
        customLabels = []
    print( 'MetaData: {0}'.format(meta_data) )
    create_dt = obj_head['LastModified']
    print( 'ABOUT TO CALL DETECT LABELS WITH: {0}, {1}'.format(key, bucket) )
    labels = detect_labels( key, bucket)
    label_count = len(labels)
    all_labels = labels + [x for x in customLabels if x not in labels]
    print( 'Labels detected: {0}'.format(label_count) )
    print( 'Labels are: {0}'.format( ', '.join(labels) ) )
    obj_data = {
        "objectKey": key,
        "bucket": bucket,
        "createdTimestamp": create_dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "labels": all_labels,
    }
    res = json.dumps( obj_data )
    return res
   
def elastic_search( query, index, url, auth ):
    # ES 6.x requires an explicit Content-Type header
    headers = { "Content-Type": "application/json" }
    # Make the signed HTTP request
    r = requests.get(url, auth=auth, headers=headers, data=json.dumps(query))
    print( 'INFO::r.text is {0}'.format(r.text))
    print( 'INFO::r.text type is {0}'.format(type(r.text)))
    try:
        search_res = json.loads(r.text)["hits"]["hits"]
    except Exception as e:
        print( 'EXCEPTION in elastic_search(): {0}'.format(e) )
        send_sms( '+14132444210', 'ElasticSearch domain {0} is out of commission at the moment. Please fix ASAP!!!'.format(index) )
        # raise Exception( 'EXCEPTION:: ElasticSearch domain {0} is out of commission at the moment.'.format(index) )
        search_res = None
    return search_res
   
def es_post( data, index, url, auth ):
    # ES 6.x requires an explicit Content-Type header
    headers = { "Content-Type": "application/json" }
    # Make the signed HTTP request
    url = url + '/' + index
    print( 'url is: {0}'.format( url ) )
    r = requests.post( url, auth=auth, headers=headers, data=data )
    print( 'INFO::r.text is {0}'.format(r.text))
    print( 'INFO::r.text type is {0}'.format(type(r.text)))
    return

def connectES(esEndPoint, auth):
    print ('Connecting to the ES Endpoint {0}'.format(esEndPoint))
    try:
        esClient = Elasticsearch(
            hosts=[{'host': esEndPoint, 'port': 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
            )
        print( 'Successful connection to the ES Endpoint: {0}'.format(esEndPoint) )
    except Exception as E:
        print("Unable to connect to {0}".format(esEndPoint))
        print(E)
    return esClient

def createIndex(esClient, index):
   
    indexDoc = {
        # "dataRecord" : {
        #     "properties" : {
        #         "objectKey" : {
        #           "type": "string"
        #         },
        #         "bucket" : {
        #             "type": "string"
        #         },
        #         "createdTimestamp" : {
        #             "type" : "date",
        #             "format" : "dateOptionalTime"
        #         },
        #         "labels" : {
        #             "type" : "string"
        #         }
        #     }
        # },
        "settings" : {
            "number_of_shards": 1,
            "number_of_replicas": 0
        }
    }
   
    try:
        res = esClient.indices.exists(index)
        print("Index Exists ... {}".format(res))
        if res is False:
            esClient.indices.create(index, body=indexDoc)
    except Exception as E:
        print("Unable to Create Index {0}".format(index))
        print(E)
       
    return

def indexDocElement(esClient, index, data):
    try:
        retval = esClient.index(index=index, body=data)
        print( "Following data indexed into {0}:\n{1}".format(index, data) )
    except Exception as E:
        print( "Doc not indexed" )
        print( "Error: {0}".format(E) )
    return retval

def lambda_handler(event, context):
    # TODO implement
    connect_endpoint = ES_ENDPOINT.split('https://')[1]
    print( 'connect_endpoint: {0}'.format(connect_endpoint) )
    esClient = connectES( ES_ENDPOINT.split('https://')[1], ('master', 'Master1!') )
    createIndex( esClient, ES_INDEX )
    print( 'Event: {0}'.format(event) )
    print( 'Context: {0}'.format(context) )
    for record in event['Records']:
        print( 'Record: {0}'.format(record) )
        bucket = record['s3']['bucket']['name']
        print('Bucket: {0}'.format(bucket) )
        obj_key = record['s3']['object']['key']
        print('File Key: {0}'.format(obj_key) )
        res = get_obj_metadata( bucket, obj_key )
        print( res )
       
        es_post_response = indexDocElement( esClient, ES_INDEX, res )
        print( "es_post_response: {0}".format(es_post_response) )
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
