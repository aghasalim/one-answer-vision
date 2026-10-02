from oav import vlm


class _Resp:
    def raise_for_status(self):
        pass

    def json(self):
        return {"response": " 42 ", "eval_count": 3}


def test_ask_tolerates_trailing_slash_in_host(tmp_path, monkeypatch):
    img = tmp_path / "x.jpg"
    img.write_bytes(b"\xff\xd8\xff\xd9")
    seen = {}

    def fake_post(url, json, timeout):
        seen["url"] = url
        return _Resp()

    monkeypatch.setattr(vlm.requests, "post", fake_post)
    r = vlm.ask(str(img), "what is it", host="http://box:11434/")
    assert seen["url"] == "http://box:11434/api/generate"
    assert r["answer"] == "42"
