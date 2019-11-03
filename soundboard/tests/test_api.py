from soundboard.client_api import JSONApi

HTTPBIN_URL = "httpbin.org/response-headers"


def test_json(httpbin):
    url = httpbin.url + "/response-headers"
    js_api = JSONApi(url, foo="bar")
    assert js_api.get().data["foo"] == "bar"
    more_js_api = JSONApi(url, foo="bar")
    assert js_api is more_js_api

    even_more_js_api = JSONApi(url, herp="derp")
    assert js_api is not even_more_js_api
