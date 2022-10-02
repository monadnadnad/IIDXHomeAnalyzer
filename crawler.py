# Infra
import chromedriver_binary # load chromedriver
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config
from player import Player

class Crawler:
    def __init__(self):
        self.session = requests.session()
    def login(self, email_address, password, cookie_fname="cookie.json"):
        """
        Seleniumを利用したログインでCookieを取得して保存する
        基本的に使わない
        """
        options = webdriver.ChromeOptions()
        # useragentを設定しないとログインページで403になる
        options.add_argument(f"user-agent={config.user_agent()}")
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver=driver, timeout=10)
        # ログインページへのアクセス
        driver.get("https://p.eagate.573.jp/gate/p/login.html?path=/")
        # フォーム入力
        driver.find_element(By.ID, "id_userId").send_keys(email_address)
        driver.find_element(By.ID, "id_password").send_keys(password)
        form = driver.find_element(By.NAME, "frm")
        form.submit()
        wait.until(EC.presence_of_all_elements_located)
        # ハードコードで簡易的な成功確認
        if driver.current_url != "https://p.eagate.573.jp/":
            raise Exception
        cookies = driver.get_cookies()
        with open(cookie_fname, "w") as f:
            json.dump(cookies, f, indent=2)
        self.set_cookies(cookies)
        driver.quit()
    def set_cookies(self, cookies: list[dict[str, str]]):
        """
        Cookieを引数から設定する
        """
        for cookie in cookies:
            self.session.cookies.set(cookie["name"], cookie["value"])
    def load_cookies(self, fname="cookie.json"):
        """
        ローカルのCookieを読み込む
        """
        with open(fname, "r") as f:
            cookies = json.load(f)
        self.set_cookies(cookies)
    def get_log(self) -> list[Player]:
        """
        ライバル検索画面からプレイヤーのリストを取得する
        """
        res = self.session.get(config.rival_search_url())
        soup = BeautifulSoup(res.text, "html.parser")
        table = soup.find(id="result")
        trs = table.find_all("tr")[1:] # ヘッダーをスキップ
        ret = []
        for tr in trs:
            tds = tr.find_all("td")
            name, id = tds[0].text, tds[1].text
            ret.append(Player(name, id))
        return ret
