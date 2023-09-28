import configparser
import json
import logging
import yadisk

from work_with_boto3 import delete_files

config = configparser.ConfigParser()
config.read("settings.ini")

oath_token = config["Yandex Disc"]['oath_token']
root_folder = config["Yandex Disc"]['root_folder']
choice_answer_number = config["Yandex Forms"]['choice_answer_number']
file_answer_number = config["Yandex Forms"]['file_answer_number']


def get_link_to_download(link) -> str:
    return str(link).replace("%2F", "/").replace("https://forms.yandex.ru/cloud/files?path=",
                                                 "https://storage.yandexcloud.net")


def upload_file(**kwargs):
    y = yadisk.YaDisk(token=oath_token)
    if not (y.check_token()):
        logging.critical("Токен указан неправильно")
        return {
            'statusCode': 401,
            'body': 'Не авторизован.',
        }

    folder_to_download = f"{root_folder}/{kwargs['folder_name']}"
    logging.critical(folder_to_download)
    if not y.is_dir(folder_to_download):
        y.mkdir(folder_to_download)

    for file in kwargs["files"]:
        file_name = file.get("name")
        file_url = file.get("path")
        y.upload_url(file_url, f"{folder_to_download}/{file_name}")
    return {
        'statusCode': 202,
        'body': 'Ok',
    }


def getter(**kwargs):
    return json.loads(kwargs["json"]["body"]).get("answer", {}).get("data", {}).get(kwargs["answer_number"], {}).get(
        "value", {})


def handler(event, context):
    logging.critical(event)
    folder_name = getter(
        json=event,
        answer_number=choice_answer_number,
    )[0].get("text")

    files = getter(
        json=event,
        answer_number=file_answer_number,
    )

    response = upload_file(
        folder_name=folder_name,
        files=files
    )

    if response['statusCode'] == 401:
        return response

    delete_files()

    return {
        'statusCode': 200,
        'body': 'OK'
    }
