import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import smtplib
import ssl
from email.mime.text import MIMEText
import os
import io

VALID_WORDS = ["招聘", "公开招聘", "事业单位", "人才引进"]
INVALID_WORDS = ["会议", "解读", "政策", "公示", "学习"]

DEGREE_WORDS = ["博士", "硕士", "研究生"]
MAJOR_WORDS = [
    "生物",
    "生命科学",
    "医药",
    "医学",
    "药学",
    "食品",
    "农学",
    "科技管理",
    "项目管理",
    "产业研究"
]

URLS = {
    "广东": "http://hrss.gd.gov.cn/gkmlpt/index",
    "湖南": "http://rst.hunan.gov.cn/rst/xxgk/zpzl/",
    "重庆": "http://rlsbj.cq.gov.cn/zwxx_182/sydw/",
    "浙江": "http://rlsbt.zj.gov.cn/col/col1229743683/index.html",
    "上海": "https://rsj.sh.gov.cn/trsrc_177/"
}

EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")


def send_email(content):
    msg = MIMEText(content, "plain", "utf-8")
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = "【附件智能筛选岗位提醒】"

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.qq.com", 465, context=context) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())


def title_valid(title):
    if len(title) < 10:
        return False
    if any(b in title for b in INVALID_WORDS):
        return False
    if any(v in title for v in VALID_WORDS):
        return True
    return False


def excel_match(content_bytes):
    try:
        df = pd.read_excel(io.BytesIO(content_bytes), sheet_name=None)
        for sheet in df.values():
            text = sheet.astype(str).to_string()

            degree_ok = any(d in text for d in DEGREE_WORDS)
            major_ok = any(m in text for m in MAJOR_WORDS)

            if degree_ok and major_ok:
                return True
    except:
        return False

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
                    detail_soup = BeautifulSoup(detail.text, "lxml")

                    # 查找 Excel 附件
                    for a in detail_soup.find_all("a"):
                        href = a.get("href")
                        if href and (href.endswith(".xlsx") or href.endswith(".xls")):
                            if not href.startswith("http"):
                                href = job_url.rstrip("/") + "/" + href.lstrip("/")

                            file_response = requests.get(href, timeout=15)

                            if excel_match(file_response.content):
                                results.append(f"{region} | {title}\n{job_url}\n")
                                break

                except:
                    continue

        except:
            continue

    if results:
        content = "\n\n".join(results)
        send_email(content)


if __name__ == "__main__":
    fetch_jobs()
