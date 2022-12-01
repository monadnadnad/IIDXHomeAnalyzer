import json
import http.cookies
import requests
from bs4 import BeautifulSoup

from config import Settings
from player import Player

settings = Settings()

class ResultTableNotFoundError(Exception):
    """
    ネットワーク以外の原因でプレイヤー表が見つからない際の例外
    """
    def __init__(self, status_code: int, html: str):
        self.status_code = status_code
        self.html = html

class Crawler:
    def __init__(self, cookie_path=settings.cookie_path):
        self.session = requests.session()
        self.cookie_path = cookie_path
    def load_cookies_string(self, cookies: str):
        """
        認証済みのcookieの文字列からcookieを設定する
        """
        cookie = http.cookies.SimpleCookie()
        cookie.load(cookies)
        for morsel in cookie.values():
            self.session.cookies.set(morsel.key, morsel)
    def load_cookies(self):
        with open(self.cookie_path, "r") as f:
            cookies = json.load(f)
        for cookie in cookies:
            self.session.cookies.set(**cookie)
    def save_cookies(self, ignore_discard=False):
        cookies = [
            dict(
                version=cookie.version,
                name=cookie.name,
                value=cookie.value,
                port=cookie.port,
                domain=cookie.domain,
                path=cookie.path,
                secure=cookie.secure,
                expires=cookie.expires,
                discard=cookie.discard,
                comment=cookie.comment,
                comment_url=cookie.comment_url,
                rfc2109=cookie.rfc2109,
                rest=cookie._rest
            )
            for cookie in self.session.cookies if not cookie.discard or ignore_discard
        ]
        with open(self.cookie_path, "w") as f:
            json.dump(cookies, f, indent=2)
    def get_log(self) -> list[Player]:
        """
        ライバル検索画面からプレイヤーのリストを取得する
        """
        res = self.session.get(settings.rival_search_url)
        soup = BeautifulSoup(res.text, "html.parser")
        table = soup.find(id="result")
        if table == None:
            # 何らかの原因で表が見つからない
            # メンテナンス中、cookieが未設定、cookieが無効になった
            raise ResultTableNotFoundError(res.status_code, res.text)
        trs = table.find_all("tr")[1:] # ヘッダーをスキップ
        ret = []
        for tr in trs:
            tds = tr.find_all("td")
            name, id = tds[0].text, tds[1].text
            ret.append(Player(name, id))
        return ret
