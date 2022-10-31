import json
from pathlib import Path
from crawler import Crawler

def test_can_set_cookies_by_string():
    c = Crawler()
    c.load_cookies_string("key=value; test=test")
    assert c.session.cookies.get("key") == "value"
    assert c.session.cookies.get("test") == "test"

def test_can_set_cookies_from_file(tmp_path: Path):
    d = tmp_path / "sub"
    d.write_text(
        """
        [
            {
                "domain": ".test.jp",
                "expires": 1667157345,
                "name": "test1",
                "path": "/",
                "secure": false,
                "value": "1"
            },
            {
                "domain": ".test.jp",
                "expires": 1667157345,
                "name": "test2",
                "path": "/",
                "secure": false,
                "value": "2"
            }
        ]"""
    )
    c = Crawler(cookie_path=str(d))
    c.load_cookies()
    assert c.session.cookies.get("test1") == "1"
    assert c.session.cookies.get("test2") == "2"

def test_can_save_cookies(tmp_path: Path):
    d = tmp_path / "sub"
    c = Crawler(cookie_path=str(d))
    c.session.cookies.set("test", "test2")
    c.save_cookies()
    should_be_json = d.read_text()
    assert should_be_json != ""
    ls = json.loads(should_be_json)
    assert len(ls) == 1
    dic = ls[0]
    assert dic["name"] == "test"
    assert dic["value"] == "test2"
