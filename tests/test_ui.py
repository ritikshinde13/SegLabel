import pytest

def test_all_ui_routes_render_ok(client):
    routes = [
        "/",
        "/workloads",
        "/events",
        "/simulator",
        "/verification",
        "/policies",
        "/audit"
    ]
    for r in routes:
        res = client.get(r)
        assert res.status_code == 200, f"Route {r} failed with {res.status_code}"
        assert b"SegLabel" in res.data or b"SEGLABEL" in res.data, f"Brand missing on route {r}"


def test_api_events_endpoint(client):
    res = client.get("/api/events")
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)
