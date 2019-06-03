# redshift-alexa-analytics

In this project, you will be able to configure alexa to query your redshift data warehouse to get answers for your business intelligence questions. 

Please make sure you have the following available.

1) Amazon Developer account (Free) Note This is different from a typical AWS workflow.
2) AWS Account with admin or full access to all services

### Instructions on configuring lambda

1) There are few environment variable that needs to be created in the lambda console in order to make the lambda work with Alexa and Redshift.

![alt text](https://raw.githubusercontent.com/tchaudhary/redshift-alexa-analytics/master/images/lambda_env_variables.png)

2) For this project, the lambda is in a private subnet so a NAT gateway was needed to be assocaited with the private subnet in order to interact with Alexa and Redshift. More information about this is here: https://aws.amazon.com/premiumsupport/knowledge-center/internet-access-lambda-function/

