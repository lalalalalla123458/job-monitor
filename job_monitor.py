import requests
from bs4 import BeautifulSoup
import datetime
import smtplib
import ssl
from email.mime.text import MIMEText
import os

KEYWORDS = ["博士", "科技", "科研", "管理", "专技", "事业单位", "人才"]

URLS = {
    "广东": "http://hrss.gd.gov.cn",
    "湖南": "http://rst.hunan.gov.cn",
    "重庆": "http://rlsbj.cq.gov.cn",
    "浙江": "http://rlsbt.zj.gov.cn",
    "上海": "https://rsj.sh.gov.cn"
}

EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")


def send_email(content):
    msg = MIMEText(content, "plain", "utf-8")
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = "【岗位提醒】今日更新"

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.qq.com", 465, context=context) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())


def fetch_jobs():
    today = datetime.date.today().strftime("%Y-%m-%d")
    results = []

    for region, url in URLS.items():
        try:
            response = requests.get(url, timeout=10)
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "lxml")

            for link in soup.find_all("a"):
                title = link.get_text().strip()
                if len(title) > 6 and any(k in title for k in KEYWORDS):
                    job_url = link.get("href")
                    if job_url and not job_url.startswith("http"):
                        job_url = url.rstrip("/") + "/" + job_url.lstrip("/")

                    results.append(f"{region} | {title}\n{job_url}\n")

        except:
            pass

    if results:
        content = "\n\n".join(results)
        send_email(content)


if __name__ == "__main__":
    fetch_jobs()
