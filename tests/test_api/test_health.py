from api.routes.health import health


def test_health_liveness_endpoint_payload():
    assert health() == {"status": "ok"}
