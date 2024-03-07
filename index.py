import configparser
import json
import logging
import requests

from work_with_boto3 import delete_files

config = configparser.ConfigParser()
config.read("settings.ini")

oath_token = config["Yandex Disc"]["oath_token"]
root_folder = config["Yandex Disc"]["root_folder"]
choice_answer_number = config["Yandex Forms"]["choice_answer_number"]
file_answer_number = config["Yandex Forms"]["file_answer_number"]


def get_link_to_download(link) -> str:
    return (
        str(link)
        .replace("%2F", "/")
        .replace(
            "https://forms.yandex.ru/cloud/files?path=",
            "https://storage.yandexcloud.net",
        )
    )


def upload_files_from_s3(folder_to_download, headers, **kwargs):
    for file in kwargs["files"]:
        logging.critical(file)
        file_name = file.get("name")
        file_url = get_link_to_download(file.get("path"))
        file_bin = requests.get(file_url).content

        params = {"path": f"{folder_to_download}/{file_name}"}
        r = requests.get(
            "https://cloud-api.yandex.net/v1/disk/resources/upload",
            headers=headers,
            params=params,
        )
        logging.critical(r)
        logging.critical(params)
        href = r.json()["href"]

        files = {"file": file_bin}
        requests.put(href, files=files)


def upload_file(**kwargs) -> dict:
    folder_to_download = f"{root_folder}/{kwargs['folder_name']}"
    headers = {"Authorization": f"OAuth {oath_token}"}
    params = {"path": folder_to_download}

    response = requests.get(
        "https://cloud-api.yandex.net/v1/disk/resources", headers=headers, params=params
    )

    if response.status_code == 401:
        logging.critical("Токен указан неправильно")
        return {
            "statusCode": 401,
            "body": "Не авторизован.",
        }

    if response.status_code == 404:
        requests.put(
            "https://cloud-api.yandex.net/v1/disk/resources",
            headers=headers,
            params=params,
        )

    upload_files_from_s3(
        **kwargs, folder_to_download=folder_to_download, headers=headers
    )
    return {
        "statusCode": 202,
        "body": "Ok",
    }


def getter(**kwargs) -> str:
    return (
        json.loads(kwargs["json"]["body"])
        .get("answer", {})
        .get("data", {})
        .get(kwargs["answer_number"], {})
        .get("value", {})
    )


def handler(event, context):
    logging.critical(event)
    folder_name = getter(
        json=event,
        answer_number=choice_answer_number,
    )[
        0
    ].get("text")

    files = getter(
        json=event,
        answer_number=file_answer_number,
    )

    response = upload_file(folder_name=folder_name, files=files)

    if response["statusCode"] == 401:
        return response

    delete_files()

    return {"statusCode": 200, "body": "OK"}
