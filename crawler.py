import json
import http.cookies
import requests
from bs4 import BeautifulSoup

import config
from player import Player

class Crawler:
    def __init__(self, cookie_path=config.cookie_path()):
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
    def save_cookies(self):
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
            ) for cookie in self.session.cookies
        ]
        with open(self.cookie_path, "w") as f:
            json.dump(cookies, f, indent=2)
    def get_log(self) -> list[Player]:
        """
        ライバル検索画面からプレイヤーのリストを取得する
        """
        res = self.session.get(config.rival_search_url())
        soup = BeautifulSoup(res.text, "html.parser")
        table = soup.find(id="result")
        if table == None:
            # 何らかの原因で表が見つからない
            # メンテナンス中、cookieが未設定、cookieが無効になった
            raise Exception("search result table not found")
        trs = table.find_all("tr")[1:] # ヘッダーをスキップ
        ret = []
        for tr in trs:
            tds = tr.find_all("td")
            name, id = tds[0].text, tds[1].text
            ret.append(Player(name, id))
        return ret
