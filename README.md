# End-to-End Anomaly Detection Model on AWS

## Opportunity Statement
A hypothetical business develops and produces edge devices that measure and control various electrical, thermal and mechanical quantities pertaining to equipment assets. The business has identified a growth opportunity to offer its customers real time analytics to its customers using the operational sensor data. One specific use case the company wants to focus on is real time anomaly detection. The goal is to enable predictive maintenance, to allow customers to preemptively respond to equipment failures, potentially saving hundreds of thousands of dollars of equipment damage. 
With thousands of sensors in current operation across the business’ customer base, the company’s challenge is to achieve the needed scale to collect, store and analyze massive amounts of customers’ sensor data (both current and new customers) and keep it available on a 24×7 basis.

## Background Information
The following provides some more information about the needs and constraints. 
1)	The analytics solution needs to be able to collect, store, process, and analyze sensor data from edge devices. It should be able to detect anomalous readings and alert maintenance personnel via. text notification in real time.
2)	Current capabilities does not support performing storage and processing on the edge.
3)	Current configuration offers a web API (server-sent events) which can be used to stream operational sensor data to the cloud.
4)	Data rates of each sensor is up to 1 record per minute, for a duration of the equipment’s life (usually 20 years)
5)	For this project, the focus is on detecting anomalies on the evaporator, which is one of the equipment used in a typical HVAC system. This anomaly takes the form of unusual spikes in the evaporator temperature. These spikes are readily distinguished from “regular” observations in a time series plot. Proactive action (e.g. changing pressure setting, temporarily increasing set point temperature etc.) if taken within the timespan of 20 minutes since the time of the anomalous event is considered a desired outcome. It can take up to 10 minutes for maintenance staff to take an action after detecting an anomoulous event. Hence, anomalous events needs to be alerted to the maintenance staff within 5-10 minutes by the analytics solution. It is calculated that by doing so, costly repairs of the asset can be prevented. The expected cost of the repairs is $100,000
6)	Prior lab tests has revealed that abnormal conditions lasting for 5 minutes or longer should prompt an alert.

## How this Opportunity was Met?
The following provides an AWS architecture to achieve the business needs.

![Architecture](https://github.com/sahilsaxena21/awsanomalydetection/blob/main/images/deployed_architecture.JPG)


### Several design choices are discussed below.

**Serverless Computing on the Cloud**

While opting for EC2 instances for processing is a possible solution, a serverless approach is opted to make management and provisioning of environment easier, while being more performant. Given the current limitations for edge computing, the data is streamed to the AWS cloud using web APIs.

**Lambda Functions**

Three Lambda functions are used. 
1.	[api_ping.py](https://github.com/sahilsaxena21/awsanomalydetection/blob/main/lambda_functions/api_ping.py) To stream real-time data from the web API to DynamoDB. 
2.	[Dynamodb2s3.py](https://github.com/sahilsaxena21/awsanomalydetection/blob/main/lambda_functions/dynamodb2s3.py) Making batch calls from DynamoDB to S3
3.	[Detect_anomaly.py](https://github.com/sahilsaxena21/awsanomalydetection/blob/main/lambda_functions/detect_anomaly.py) Activate SNS for anomaly conditions

Lambda functions are used for several reasons:
-	The functions do not require heavy processing to warrant use of EC2 instances. All functions are executable in less than 900 seconds, and less than 128 MB memory allocation
-	Its serverless. Minimal management and provisioning of environment
-	Its cost efficient. Low costs at $0.20 / million requests and 0.00001667 per GB/second
-	One disadvantage to be noted is that it does not have a built-in retries and failure notifications capabilities (e.g. Data Pipelines). But error handling can be readily customized within the lambda function code. The example code does not include this, but this can be readily coded by invoking AWS X-Ray.
-	High availability, high scalability and high performance

**DynamoDB**

DynamoDB is used for real-time hot storage and for storing anomaly cut off values updated by the Sagemaker RCF algorithm
![Database Model]( https://github.com/sahilsaxena21/awsanomalydetection/blob/main/images/ERD.JPG)

DynamoDB is used for several reasons:

-	High-performance reads and writes are easy to manage with DynamoDB (OLTP workload)
-	Filtering using Range Keys: Range/sort key option is used for both stream data and the anomaly cut off table. For the stream data, the option is available to improve the model’s performance by only training models on the most recent sensor data. For the anomaly cut off values, the latest anomaly cut off value is read by the lambda function to decide if a set of observations are anomalous.
-	Highly available at all times without manual intervention, high level of data durability

**Amazon Random Cut Forests (RCF) for Anomaly Detection**

Note: With each data point, RCF associates an anomaly score. Low score values indicate that the data point is considered "normal." High values indicate the presence of an anomaly in the data. The definitions of "low" and "high" depend on the application, but common practice suggests that scores beyond three standard deviations from the mean score are considered anomalous.
[Detected Anomalous Readings by RCF]( https://github.com/sahilsaxena21/awsanomalydetection/blob/main/images/anomaly_detection.JPG)
-	Designed to detect unexpected spikes in time series data, breaks in periodicity, or unclassifiable data points. This aligns with the needs of the business.
-	Designed to work with arbitrary-dimensional input, allowing opportunities to scale the model to other anomalous readings in future projects.
-	In this use case, a more conservative approach is taken by using 2.5 standard deviations from the mean score as the cut off for anomalous readings. This is due to the preference of prioritizing recall over precision. In this case, the cost of a false negative far outweighs the cost of a false positive. Further lab tests are planned in the future to further optimize this cut off value. 
