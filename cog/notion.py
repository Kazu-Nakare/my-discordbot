# import requests
import requests
import io
import re
import time
from notion_client import Client

NOTION_API_KEY = ""
notion = Client(auth=NOTION_API_KEY)

DATABASE_ID = ""  # カリキュラムのDBID


def db_fetch():
    sorts = {"sorts": [
        {
            "property": "開講日時",
            "direction": "descending"
        }
    ]}
    return notion.databases.query(DATABASE_ID, **sorts)


def pg_fetch(PAGE_ID):
    return notion.pages.retrieve(PAGE_ID)


def test(curriculum_url: str):
    pattern = re.compile(r"(\d|[a-f]){32}")
    ID = pattern.search(curriculum_url).group()
    CURRICULUM_ID = f"{ID[:8]}-{ID[8:12]}-{ID[12:16]}-{ID[16:20]}-{ID[20:]}"

    curriculum_response = notion.pages.retrieve(CURRICULUM_ID)
    WORK_ID = curriculum_response["properties"]["作品"]["relation"][0]["id"]

    print("waiting...")
    time.sleep(1)
    work_response = notion.pages.retrieve(WORK_ID)

    return curriculum_response, work_response


r = db_fetch()
print(r)
