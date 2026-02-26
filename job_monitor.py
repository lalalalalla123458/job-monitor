import requests
from bs4 import BeautifulSoup
import smtplib
import ssl
from email.mime.text import MIMEText
import os

# ========= 标题判断 =========

VALID_WORDS = ["招聘", "公开招聘", "事业单位", "人才引进", "招录"]
INVALID_WORDS = ["会议", "解读", "政策解读", "公示结果"]

# ========= 专业匹配关键词 =========

MATCH_WORDS = [
    # 生物医药
    "生物", "生命科学", "医学", "医药", "药学",
    "食品", "农学", "检验", "检测",
    "医疗器械", "质量", "安全",

    # 医院系统
    "医院", "临床", "科研岗", "行政岗",
    "医技", "病理", "实验室", "医学检验",

    # 监管系统
    "市场监督", "药品监督", "食品药品",
    "海关", "出入境", "疾控", "卫生监督",
    "科技管理", "科研", "技术岗", "管理岗"
]

# ========= 监控入口 =========

URLS = {
    # 人社
    "广东人社": "http://hrss.gd.gov.cn/gkmlpt/index",
    "湖南人社": "http://rst.hunan.gov.cn/rst/xxgk/zpzl/",
    "重庆人社": "http://rlsbj.cq.gov.cn/zwxx_182/sydw/",
    "浙江人社": "http://rlsbt.zj.gov.cn/col/col1229743683/index.html",
    "上海人社": "https://rsj.sh.gov.cn/trsrc_177/",

    # 药监 / 市监
    "广东药监": "http://mpa.gd.gov.cn/",
    "湖南药监": "http://mpa.hunan.gov.cn/",
    "上海药监": "https://yjj.sh.gov.cn/",
    "重庆市场监管": "http://scjgj.cq.gov.cn/",

    # 海关
    "海关总署": "http://www.customs.gov.cn/",

    # 卫健委
    "广东卫健委": "http://wsjkw.gd.gov.cn/",
    "湖南卫健委": "http://wjw.hunan.gov.cn/",
    "上海卫健委": "https://wsjkw.sh.gov.cn/",

    # 三甲医院示例
    "中山大学附属第一医院": "https://www.gzsums.net/",
    "湘雅医院": "https://www.xyeyy.com/",
    "上海瑞金医院": "https://www.rjh.com.cn/"
}

EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def send_email(content):
    msg = MIMEText(content, "plain", "utf-8")
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = "【岗位监控提醒-医院扩展版】"

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
            response = requests.get(url, headers=HEADERS, timeout=15)
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
                    job_url = requests.compat.urljoin(url, job_url)

                try:
                    detail = requests.get(job_url, headers=HEADERS, timeout=15)
                    detail.encoding = "utf-8"
                    text = detail.text

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
