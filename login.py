import chromedriver_binary
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from crawler import Crawler

if __name__ == "__main__":
    driver = webdriver.Chrome()
    try:
        # ログインページへのアクセス
        driver.get("https://p.eagate.573.jp/gate/p/login.html?path=/")
        # 2分以内にホームかマイページに遷移することで成功確認
        WebDriverWait(
            driver=driver,
            timeout=120.0
        ).until(EC.any_of(
            EC.url_to_be("https://p.eagate.573.jp/"),
            EC.url_to_be("https://p.eagate.573.jp/gate/p/mypage/index.html")
        ))
        # Cookieの保存
        cookies = driver.get_cookies()
        # 保存の機能を委譲
        c = Crawler()
        for cookie in cookies:
            # selenium -> requestsに変換
            attributes = {"domain": cookie["domain"], "path": cookie["path"]}
            if "expiry" in cookie:
                attributes["expires"] = cookie["expiry"]
            if "secure" in cookie:
                attributes["secure"] = cookie["secure"]
            if "httpOnly" in cookie:
                attributes["rest"] = {"HttpOnly": cookie["httpOnly"]}
            c.session.cookies.set(cookie["name"], cookie["value"], **attributes)
        c.save_cookies(ignore_discard=True)
    finally:
        driver.quit()