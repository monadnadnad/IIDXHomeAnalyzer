from fetcher import Fetcher

def test_can_set_cookies_by_string():
    c = Fetcher()
    c.load_cookies_string("key=value; test=test")
    assert c.session.cookies.get("key") == "value"
    assert c.session.cookies.get("test") == "test"
