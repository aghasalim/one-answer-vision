from unittest import mock

from PIL import Image

from oav import cli, vlm


def _fake_post(url, json, timeout):
    r = mock.Mock()
    r.json.return_value = {"response": "  180\n", "eval_count": 3}
    r.raise_for_status.return_value = None
    _fake_post.last = json
    return r


def test_ask_cli_prints_answer_only(tmp_path, capsys):
    img = tmp_path / "x.png"
    Image.new("RGB", (32, 32), "white").save(img)
    with mock.patch.object(vlm.requests, "post", _fake_post):
        cli.main(["ask", str(img), "what temperature", "--model", "fake"])
    assert capsys.readouterr().out == "180\n"
    body = _fake_post.last
    assert body["model"] == "fake"
    assert body["options"]["temperature"] == 0
    assert "what temperature" in body["prompt"]
    assert len(body["images"]) == 1


def test_ask_cli_time_flag(tmp_path, capsys):
    img = tmp_path / "x.png"
    Image.new("RGB", (32, 32), "white").save(img)
    with mock.patch.object(vlm.requests, "post", _fake_post):
        cli.main(["ask", str(img), "q", "--time"])
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "180" and out[1].endswith("seconds")
