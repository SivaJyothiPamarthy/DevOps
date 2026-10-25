from pathlib import Path

from analyze import analyze, render

SAMPLE = Path(__file__).with_name("sample_access.log")


def test_sample_log():
    r = analyze(SAMPLE.read_text().splitlines())
    assert r.total == 10
    assert r.malformed == 1
    assert r.ips.most_common(1) == [("10.0.0.1", 4)]
    assert round(r.error_rate_5xx, 4) == round(2 / 10, 4)
    assert r.percentile(95) == 2.501
    ep, _ = r.slowest_endpoint()
    assert ep == "POST /api/v1/orders"
    # query strings grouped with the base path
    assert len(r.endpoint_latency["GET /api/v1/orders"]) == 6
    assert "Total requests : 10" in render(r)


def test_empty_input():
    r = analyze([])
    assert r.total == 0 and r.error_rate_5xx == 0 and r.percentile(95) == 0
    assert r.slowest_endpoint() is None
