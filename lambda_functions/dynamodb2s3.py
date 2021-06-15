# -*- coding: utf-8 -*-
"""Untitled16.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1xtBzHjoPFa625fsV--3CN8MIzJvOevIV
"""

#lambda function dynamodb_to_s3

import csv
import boto3
import json

TABLE_NAME = 'HVACData'
#this function creates a replica of the dynamodb table on s3 named data.csv. This is done every 10 days for the sagemaker model training

OUTPUT_BUCKET = 'serverlessapphvac323'
TEMP_FILENAME = '/tmp/data.csv'
OUTPUT_KEY = 'data.csv'

s3_resource = boto3.resource('s3')
dynamodb_resource = boto3.resource('dynamodb')
table = dynamodb_resource.Table(TABLE_NAME)

def lambda_handler(event, context):

    with open(TEMP_FILENAME, 'w') as output_file:
        writer = csv.writer(output_file)
        header = True
        first_page = True

        # Paginate results
        while True:

            # Scan DynamoDB table
            if first_page:
                response = table.scan()
                first_page = False
            else:
                response = table.scan(ExclusiveStartKey = response['LastEvaluatedKey'])

            for item in response['Items']:

                # Write header row?
                if header:
                    writer.writerow(item.keys())
                    header = False

                writer.writerow(item.values())

            # Last page?
            if 'LastEvaluatedKey' not in response:
                break

    # Upload temp file to S3
    s3_resource.Bucket(OUTPUT_BUCKET).upload_file(TEMP_FILENAME, OUTPUT_KEY)