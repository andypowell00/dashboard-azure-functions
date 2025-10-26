# Dockerfile
FROM mcr.microsoft.com/azure-functions/python:4-python3.12

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

COPY . /home/site/wwwroot
WORKDIR /home/site/wwwroot

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
