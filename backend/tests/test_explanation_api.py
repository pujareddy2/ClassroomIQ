import asyncio
import uuid

import httpx

from app.main import app


async def _request(path: str, method: str = "GET", payload: dict | None = None):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        request = getattr(client, method.lower())
        if payload is None:
            return await request(path)
        return await request(path, json=payload)


def test_explanation_routes_are_registered():
    fake_lecture_id = str(uuid.uuid4())

    response = asyncio.run(_request(f"/api/v1/explanations/{fake_lecture_id}"))
    assert response.status_code == 200
    envelope = response.json()
    assert envelope["status"] == "SUCCESS"
    assert envelope["data"]["lecture_id"] == fake_lecture_id

    response = asyncio.run(
        _request(
            "/api/v1/explanations/generate",
            method="POST",
            payload={"lecture_id": str(uuid.uuid4())},
        )
    )
    assert response.status_code in {200, 201, 400, 404, 409}
