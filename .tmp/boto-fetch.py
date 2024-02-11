import botocore, boto3
from botocore.session import get_session
import os, requests, json

global awsauth, session
def refresh_external_credentials():
    credentials = boto3.Session().get_credentials()
    creds = {
        "access_key": credentials.access_key,
        "secret_key": credentials.secret_key,
        "token": credentials.token,
        "expiry_time": credentials._expiry_time.isoformat()
    }
    return creds


def new_session():
    credentials = botocore.credentials.RefreshableCredentials.create_from_metadata(
        metadata=refresh_external_credentials(),
        refresh_using=refresh_external_credentials,
        method="shared-credentials-file"
    )
    session = get_session()
    session._credentials = credentials
    # session.set_config_variable("region", region_name)
    autorefresh_session = boto3.session.Session(botocore_session=session)
    session=autorefresh_session
    return session

new_session = new_session()
print(new_session.region_name)
print(new_session.get_credentials().access_key)
print(new_session.get_credentials().secret_key)
print(new_session.get_credentials().token)
print(new_session.get_credentials().expiry_time.isoformat())


another_session = refresh_external_credentials()
print(another_session['access_key'])
print(another_session['secret_key'])
print(another_session['token'])
    
