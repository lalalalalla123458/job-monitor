import requests
from bs4 import BeautifulSoup
import smtplib
import ssl
from email.mime.text import MIMEText
import os

VALID_WORDS = ["招聘", "公开招聘", "事业单位", "人才引进"]
INVALID_WORDS = ["会议", "解读", "政策解读", "公示结果"]

MATCH_WORDS = [
    "生物", "生命科学", "医药", "医学", "药学",
    "食品", "农学", "医疗器械",
    "市场监督", "药品监管", "食品药品",
    "质量监督", "科研", "技术", "管理"
]

URLS = {
    "广东人社": "http://hrss.gd.gov.cn/gkmlpt/index",
    "湖南人社": "http://rst.hunan.gov.cn/rst/xxgk/zpzl/",
    "重庆人社": "http://rlsbj.cq.gov.cn/zwxx_182/sydw/",
    "浙江人社": "http://rlsbt.zj.gov.cn/col/col1229743683/index.html",
    "上海人社": "https://rsj.sh.gov.cn/trsrc_177/"
}

EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")


def send_email(content):
    msg = MIMEText(content, "plain", "utf-8")
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = "【岗位监控提醒-放宽版】"

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.qq.com", 465, context=context) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())


def title_valid(title):
    if len(title) < 6:
        return False
    if any(b in title for b in INVALID_WORDS):
        return False
    if any(v in title for v in VALID_WORDS):
        return True
    return False


def fetch_jobs():
    results = []

    for region, url in URLS.items():
        try:
            response = requests.get(url, timeout=10)
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "lxml")

            for link in soup.find_all("a"):
                title = link.get_text().strip()

                if not title_valid(title):
                    continue

                job_url = link.get("href")
                if not job_url:
                    continue

                if not job_url.startswith("http"):
                    job_url = url.rstrip("/") + "/" + job_url.lstrip("/")

                try:
                    detail = requests.get(job_url, timeout=10)
                    detail.encoding = "utf-8"
                    text = detail.text

                    # 放宽条件：只要出现一个关键词
                    if any(word in text for word in MATCH_WORDS):
                        results.append(f"{region} | {title}\n{job_url}\n")

                except:
                    continue

        except:
            continue

    if results:
        content = "\n\n".join(results)
        send_email(content)


if __name__ == "__main__":
    fetch_jobs()
