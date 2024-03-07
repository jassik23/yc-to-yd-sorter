import boto3
import configparser

config = configparser.ConfigParser()
config.read("settings.ini")


def delete_files():
    s3 = boto3.client(
        service_name="s3",
        endpoint_url="https://storage.yandexcloud.net",
        aws_access_key_id=config["Yandex Cloud"]["aws_access_key_id"],
        aws_secret_access_key=config["Yandex Cloud"]["aws_secret_access_key"],
    )
    bucket_name = config["Yandex Cloud"]["bucket_name"]
    objects = s3.list_objects(Bucket=bucket_name)
    for object in objects["Contents"]:
        s3.delete_object(Bucket=bucket_name, Key=object["Key"])
