import json
import boto3
import datetime
import requests
from requests_aws4auth import AWS4Auth
from elasticsearch import Elasticsearch, RequestsHttpConnection

def detect_labels(img):

    client=boto3.client('rekognition')

    response = client.detect_labels(Image=img,
        MaxLabels=10, , MinConfidence=75)
        
    labels = []
    for label in response['Labels']:
        labels.append(label['Name'])

    return labels

def lambda_handler(event, context):

    # get bucket name, image name and extract labels
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    photo = event["Records"][0]["s3"]["object"]["key"]
    img = {'S3Object':{'Bucket':bucket,'Name':photo}}
    labels = detect_labels(img)
    
    # meta-data given by user during upload
    client = boto3.client("s3")
    image_meta_data = client.head_object(Bucket=bucket, Key=photo)
    
    image_meta_data_labels_list = (image_meta_data["Metadata"]["customlabels"]).split(",")

    # append user specified labels to labels list returned by rekognition service
    for label in image_meta_data_labels_list:
        labels.append(label)

    print("Labels detected: " + str(labels))
    
    # create json object to be sent to elastic search domain
    es_obj = {
        "objectKey": photo,
        "bucket": bucket,
        "createdTimestamp": str(datetime.datetime.now().isoformat()),
        "labels": labels
    }

    print(json.dumps(es_obj))

   # elastic search domain to hit
    es = 'search-search-photos-2lt6xlp5nykp6766sn77hsktxu.us-east-1.es.amazonaws.com'
    index = 'photos'
    url = 'https://' + es + '/' + index + '/_doc/'

    region = 'us-east-1'  # For example, us-west-1
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

    hders = {"Content-Type": "application/json"}

    req = requests.post(url, auth=awsauth, headers=hders, data=json.dumps(es_obj))
    print(req)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
