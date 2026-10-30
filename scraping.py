
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.robotparser import RobotFileParser
from collections import deque
import time
import csv

# 武蔵野大学のトップページ
START_URL = "https://www.musashino-u.ac.jp/"
DOMAIN = urlparse(START_URL).netloc

# アクセス間隔（秒）
SLEEP_TIME = 2

# テスト時は10、全ページ取得時はNone
MAX_PAGES = None

USER_AGENT = "UniversitySiteMapStudy/1.0"

# URLをkey、タイトルをvalueとする辞書
pages = {}

# アクセス済みURL
visited = set()

# アクセス予定URL
queue = deque([START_URL])
queued = {START_URL}

# HTTPセッション
session = requests.Session()
session.headers.update({
    "User-Agent": USER_AGENT
})

# robots.txtを確認
robots_url = urljoin(START_URL, "/robots.txt")
robots = RobotFileParser()
robots.set_url(robots_url)

try:
    time.sleep(SLEEP_TIME)
    robots_response = session.get(robots_url, timeout=15)

    if robots_response.status_code == 200:
        robots.parse(robots_response.text.splitlines())
        print("robots.txtを読み込みました。")
    elif robots_response.status_code == 404:
        robots.parse([])
        print("robots.txtは見つかりませんでした。")
    else:
        print("robots.txtを確認できませんでした。")
        raise SystemExit(1)

except requests.RequestException as e:
    print("robots.txtの確認に失敗しました:", e)
    raise SystemExit(1)

print("スクレイピング開始")

# Webページを順番に取得
while queue:

    if MAX_PAGES is not None and len(visited) >= MAX_PAGES:
        break

    url = queue.popleft()
    queued.discard(url)

    if url in visited:
        continue

    visited.add(url)

    # 同一ドメインか確認
    parsed = urlparse(url)

    if parsed.netloc != DOMAIN:
        continue

    if parsed.scheme not in ("http", "https"):
        continue

    # robots.txtのルールを確認
    if not robots.can_fetch(USER_AGENT, url):
        print("robots.txtによりスキップ:", url)
        continue

    # サーバーへの負荷を軽減
    time.sleep(SLEEP_TIME)

    try:
        response = session.get(
            url,
            timeout=15,
            allow_redirects=False
        )

        # リダイレクトを処理
        if response.status_code in (301, 302, 303, 307, 308):
            location = response.headers.get("Location")

            if location:
                redirect_url = urljoin(url, location)
                redirect_url, _ = urldefrag(redirect_url)

                if (
                    urlparse(redirect_url).netloc == DOMAIN
                    and redirect_url not in visited
                    and redirect_url not in queued
                ):
                    queue.append(redirect_url)
                    queued.add(redirect_url)

            continue

        # アクセス制限時は停止
        if response.status_code in (429, 503):
            print("サーバーからアクセス制限を受けました。")
            break

        response.raise_for_status()

        # HTMLのみ処理
        content_type = response.headers.get(
            "Content-Type", ""
        ).lower()

        if "text/html" not in content_type:
            continue

        # HTMLを解析
        soup = BeautifulSoup(
            response.content,
            "html.parser"
        )

        # titleを取得
        if soup.title:
            title = soup.title.get_text(
                " ", strip=True
            )
        else:
            title = ""

        # 辞書に保存
        pages[url] = title

        print(f"{len(pages)}: {url}")
        print(f"Title: {title}")

        # ページ内のリンクを取得
        for a in soup.find_all("a", href=True):

            link = urljoin(url, a["href"])
            link, _ = urldefrag(link)

            parsed_link = urlparse(link)

            # 同一ドメインのHTTP(S)リンクのみ
            if (
                parsed_link.scheme in ("http", "https")
                and parsed_link.netloc == DOMAIN
                and link not in visited
                and link not in queued
            ):
                queue.append(link)
                queued.add(link)

    except requests.RequestException as e:
        print(f"Error: {url} - {e}")

# CSVファイルに保存
with open(
    "sitemap.csv",
    "w",
    newline="",
    encoding="utf-8-sig"
) as f:

    writer = csv.writer(f)

    writer.writerow(["URL", "Title"])

    for url, title in pages.items():
        writer.writerow([url, title])

print("----------------------------")
print("スクレイピング完了")
print(f"取得ページ数: {len(pages)}")
print("保存ファイル: sitemap.csv")
