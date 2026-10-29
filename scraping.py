
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import time
import csv

# 武蔵野大学のトップページ
start_url = "https://www.musashino-u.ac.jp/"
domain = urlparse(start_url).netloc

# URLとタイトルを保存する辞書
pages = {}

# アクセス済みURL
visited = set()

# アクセス予定のURL
queue = [start_url]

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; UniversitySiteMapStudy/1.0)"
})

# Webページを順番に取得
while queue:
    url = queue.pop(0)

    if url in visited:
        continue

    visited.add(url)

    # サーバーへの負荷を軽減
    time.sleep(2)

    try:
        response = session.get(url, timeout=15)
        response.raise_for_status()

        # HTML以外は処理しない
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            continue

        soup = BeautifulSoup(response.content, "html.parser")

        # titleを取得
        title = soup.title.get_text(strip=True) if soup.title else ""

        # 辞書に保存
        pages[url] = title
        print(f"{len(pages)}: {url} | {title}")

        # ページ内のリンクを取得
        for a in soup.find_all("a", href=True):
            link = urljoin(url, a["href"])
            link, _ = urldefrag(link)

            parsed = urlparse(link)

            # 同一ドメインのみ
            if parsed.scheme in ("http", "https") and parsed.netloc == domain:
                if link not in visited and link not in queue:
                    queue.append(link)

    except requests.RequestException as e:
        print(f"Error: {url} - {e}")

# CSVファイルに保存
with open("sitemap.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["URL", "Title"])

    for url, title in pages.items():
        writer.writerow([url, title])

print(f"完了！{len(pages)}ページを保存しました。")
