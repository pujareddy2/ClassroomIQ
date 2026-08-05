"""Contract tests for the public v1 HTTP boundary."""

from fastapi.testclient import TestClient
from concurrent.futures import ThreadPoolExecutor

from app.main import app


client = TestClient(app)


def test_health_is_a_standard_success_envelope_and_echoes_request_id():
    response = client.get("/health", headers={"X-Request-ID": "contract-test-1"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "SUCCESS"
    assert body["metadata"]["request_id"] == "contract-test-1"
    assert body["metadata"]["api_version"] == "v1"
    assert isinstance(body["metadata"]["execution_time"], float)


def test_validation_errors_use_the_standard_error_envelope():
    response = client.get("/api/v1/coverage/not-a-uuid/summary")
    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "ERROR"
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["metadata"]["request_id"]


def test_missing_bearer_token_uses_the_standard_error_envelope():
    from app.api.auth import get_current_user

    app.dependency_overrides.pop(get_current_user, None)
    response = client.get("/api/v1/coverage/not-a-uuid/summary")
    assert response.status_code == 401
    body = response.json()
    assert body["status"] == "ERROR"
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_concurrent_health_requests_keep_request_correlation_isolated():
    def request(index: int):
        return client.get("/health", headers={"X-Request-ID": f"parallel-{index}"}).json()

    with ThreadPoolExecutor(max_workers=8) as pool:
        bodies = list(pool.map(request, range(16)))

    assert {body["metadata"]["request_id"] for body in bodies} == {f"parallel-{index}" for index in range(16)}


def test_openapi_documents_the_standard_contract_for_every_v1_operation():
    schema = client.get("/openapi.json").json()
    assert "ApiEnvelope" in schema["components"]["schemas"]
    for path, operations in schema["paths"].items():
        if not path.startswith("/api/v1"):
            continue
        for method, operation in operations.items():
            if method in {"get", "post", "put", "patch", "delete"}:
                assert "422" in operation["responses"]
                assert "500" in operation["responses"]
