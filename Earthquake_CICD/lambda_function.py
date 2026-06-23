import json
import urllib.request
import boto3
from botocore.exceptions import ClientError

TABLE_NAME = "EarthquakeData"

dynamodb_client = boto3.client("dynamodb")
dynamodb = boto3.resource("dynamodb")


def create_table():
    try:
        dynamodb_client.describe_table(TableName=TABLE_NAME)

    except ClientError:

        dynamodb_client.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {
                    "AttributeName": "id",
                    "KeyType": "HASH"
                }
            ],
            AttributeDefinitions=[
                {
                    "AttributeName": "id",
                    "AttributeType": "S"
                }
            ],
            BillingMode="PAY_PER_REQUEST"
        )

        waiter = dynamodb_client.get_waiter("table_exists")
        waiter.wait(TableName=TABLE_NAME)


def lambda_handler(event, context):

    # Create table automatically if it doesn't exist
    create_table()

    table = dynamodb.Table(TABLE_NAME)

    url = (
        "https://earthquake.usgs.gov/fdsnws/event/1/query"
        "?format=geojson"
        "&limit=20"
        "&orderby=time"
    )

    response = urllib.request.urlopen(url)

    data = json.loads(response.read())

    count = 0

    for quake in data["features"]:

        properties = quake["properties"]

        item = {

            "id": quake["id"],

            "place": str(properties.get("place", "")),

            "magnitude": str(properties.get("mag", "")),

            "time": str(properties.get("time", "")),

            "status": str(properties.get("status", "")),

            "type": str(properties.get("type", ""))

        }

        table.put_item(Item=item)

        count += 1

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "Earthquake data stored successfully",
                "records_inserted": count
            }
        )
    }
