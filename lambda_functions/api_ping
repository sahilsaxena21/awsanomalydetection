# -*- coding: utf-8 -*-
"""api_ping_lambda.ipynb

"""

import requests
from requests.auth import HTTPBasicAuth
import boto3
import decimal

def get_single_entry(event=None, context=None):

  #instantiate dynamodb
  item = None
  dynamo_db = boto3.resource('dynamodb')
  table = dynamo_db.Table('HVACData')

  #api-call
  response = requests.get("https://34.226.114.9:9003/api/v1/instruments/1/values?codes=https://34.226.114.9:9003/api/v1/instruments/1/values?codes=Sensor1,Sensor2,Sensor3,CurrentSetpoint,SetpointRelativeTemp,Hourmeter,IsOutputRefr,IsOutputFan,IsOutputDefr1,IsOutputBuzzer,IsDig1,IsDig2,IsOpenDoor,ProcessStatus", 
                        auth=HTTPBasicAuth('adminapi', 'admin'), verify = False)
  response_results = response.json()["results"]
  date_time = response_results[0]["values"][0]["date"]
  evaporator_temp = response_results[0]["values"][0]["value"]
  sensor_3 = response_results[1]["values"][0]["value"]
  set_point_relative = response_results[-1]["values"][0]["value"]

  #write result to table
  with table.batch_writer() as batch_writer:
    batch_writer.put_item(                        
        Item = {
                        'Timestamp': date_time,
                        'EvaporatorTemperature': evaporator_temp,
                        'SensorTemperature':sensor_3 ,
                        'SetPointTemperature': set_point_relative,
                }
    )

  return "All clear"
