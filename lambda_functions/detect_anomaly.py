# -*- coding: utf-8 -*-
"""detect_anomaly.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1dpLlyw8daDd5TSfU8VtwVqREqw1T5tVT
"""

from __future__ import print_function
import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
import numpy as np
import json
import io
import base64


print("Starting Lambda Function.... ")
sagemaker = boto3.client('sagemaker-runtime', region_name ='us-east-1' )
dynamodb_table = boto3.resource('dynamodb', region_name='us-east-1').Table('anomaly_cutoff')

#sns config
client = boto3.client('sns')
topic_arn = 'arn:aws:sns:us-east-1:321094973998:AnomalyAlarm'

def lambda_handler(event, context):
    #initiate anomaly count variable 
    anomaly_count = 0

    #for storing latest sensor readings
    signal_data = []
        
    for record in event['Records']:
        ## filter only INSERT or MODIFY event and add to "transaction_data" dictionary 
        if record['eventName'] == "INSERT" or record['eventName'] == "MODIFY":
            temperature = record['dynamodb']['NewImage']['EvaporatorTemperature']['N']
            signal_data.append(float(temperature))
    print("transaction_data: " , signal_data) 

    #read new temperature readings as array and then convert to csv format for RCF model
    data = np.array(signal_data).reshape(-1, 1)
    csv = io.BytesIO()
    np.savetxt(csv, data, delimiter=",", fmt="%g")
    payload = csv.getvalue().decode().rstrip()

    #obtain predictions from model
    response = sagemaker.invoke_endpoint(EndpointName = 'randomcutforest-2021-06-13-02-55-23-660',
                                       ContentType = "text/csv",
                                      Body=payload)
    scores_result = json.loads(response['Body'].read().decode())

    #read the latest trained model cutoff value
    response = dynamodb_table.query(
              Limit = 1,
              ScanIndexForward = False,
              KeyConditionExpression=Key('data_kind').eq('sensor_data') & Key('update_time').lte('9999990000000000')
           )
    score_cutoff = response['Items'][0]['score_cutoff'] 
    print("score_cutoff : " + str(score_cutoff) )       
    
    #if prediction anomaly score is more than cut-off, alert anomaly!
    for index in range(len(scores_result['scores'])):
      if scores_result['scores'][index]['score'] > score_cutoff:
        anomaly_count += 1
        print("Detected abnormal temperature of: {} , with EvaporatorTemperature Cut off Value of : {}".format(scores_result['scores'][index]['score'], score_cutoff))

    #send alert only if 5 consecutive data points are found to be anomalous
    if anomaly_count >= 5:
      #send notification
      try:
          client.publish(TopicArn=topic_arn, Message='Investigate anomalous sensor readings', Subject='Anomaly Detected')
          print('Successfully delivered alarm message')
      except Exception:
          print('Delivery failure')
              
    return 'Successfully processed {} records.'.format(len(event['Records']))