"""
Comprehensive test suite for the multi-agent research API.

Tests cover all endpoints, request validation, and error handling.
"""

import pytest
from fastapi.testclient import TestClient

from app import app, SolveRequest, HealthResponse, IndexResponse, SolveResponse


@pytest.fixture
def client():
    """Fixture to provide a test client for the FastAPI app."""
    return TestClient(app)


class TestIndexEndpoint:
    """Tests for GET / endpoint."""

    def test_index_returns_200(self, client):
        """Test that GET / returns 200 OK."""
        response = client.get("/")
        assert response.status_code == 200

    def test_index_response_structure(self, client):
        """Test that GET / response has correct structure."""
        response = client.get("/")
        data = response.json()

        assert "service" in data
        assert "status" in data
        assert "endpoints" in data
        assert "message" in data

    def test_index_service_name(self, client):
        """Test that service name is correct."""
        response = client.get("/")
        data = response.json()

        assert data["service"] == "multi-agent-research"
        assert data["status"] == "ok"

    def test_index_lists_all_endpoints(self, client):
        """Test that all endpoints are listed."""
        response = client.get("/")
        data = response.json()

        endpoints = data["endpoints"]
        assert "GET /" in endpoints
        assert "GET /health" in endpoints
        assert "GET /solve" in endpoints
        assert "POST /solve" in endpoints

    def test_index_response_validation(self, client):
        """Test that response validates against IndexResponse model."""
        response = client.get("/")
        # Should not raise validation error
        IndexResponse(**response.json())


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_health_returns_200(self, client):
        """Test that GET /health returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client):
        """Test that GET /health response has correct structure."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "service" in data

    def test_health_status_ok(self, client):
        """Test that health status is 'ok'."""
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "ok"
        assert data["service"] == "multi-agent-research"

    def test_health_response_validation(self, client):
        """Test that response validates against HealthResponse model."""
        response = client.get("/health")
        # Should not raise validation error
        HealthResponse(**response.json())


class TestSolveGetEndpoint:
    """Tests for GET /solve endpoint."""

    def test_solve_get_returns_200(self, client):
        """Test that GET /solve returns 200 OK."""
        response = client.get("/solve")
        assert response.status_code == 200

    def test_solve_get_response_structure(self, client):
        """Test that GET /solve response explains the endpoint."""
        response = client.get("/solve")
        data = response.json()

        assert "status" in data
        assert "message" in data
        assert "example" in data

    def test_solve_get_method_not_allowed_status(self, client):
        """Test that GET /solve indicates method not allowed."""
        response = client.get("/solve")
        data = response.json()

        assert data["status"] == "method_not_allowed"
        assert "POST" in data["message"].upper()

    def test_solve_get_provides_example(self, client):
        """Test that GET /solve provides a usage example."""
        response = client.get("/solve")
        data = response.json()

        assert data["example"]["problem"]


class TestSolvePostEndpoint:
    """Tests for POST /solve endpoint."""

    def test_solve_post_requires_json(self, client):
        """Test that POST /solve requires JSON content-type."""
        response = client.post("/solve", data="not json")
        assert response.status_code in (400, 422)

    def test_solve_post_requires_problem_field(self, client):
        """Test that POST /solve requires 'problem' field."""
        response = client.post("/solve", json={})
        assert response.status_code == 422

    def test_solve_post_rejects_empty_problem(self, client):
        """Test that empty 'problem' is rejected."""
        response = client.post("/solve", json={"problem": ""})
        assert response.status_code == 422

    def test_solve_post_rejects_whitespace_only_problem(self, client):
        """Test that whitespace-only 'problem' is rejected."""
        response = client.post("/solve", json={"problem": "   "})
        assert response.status_code == 422

    def test_solve_post_rejects_non_string_problem(self, client):
        """Test that non-string 'problem' is rejected."""
        response = client.post("/solve", json={"problem": 123})
        assert response.status_code == 422

        response = client.post("/solve", json={"problem": None})
        assert response.status_code == 422

        response = client.post("/solve", json={"problem": ["list"]})
        assert response.status_code == 422

    def test_solve_post_accepts_valid_problem(self, client):
        """Test that valid problem is accepted by validation."""
        # This will fail with 503 if LLM is not configured, but validation passes
        response = client.post(
            "/solve",
            json={"problem": "What is 2 + 2?"}
        )
        # Should either succeed (200) or fail with LLM unavailable (503), not validation error (422)
        assert response.status_code in (200, 503)

    def test_solve_post_error_on_missing_llm(self, client):
        """Test that POST /solve returns 503 when LLM unavailable."""
        # Without OPENAI_API_KEY set, this should fail gracefully
        response = client.post(
            "/solve",
            json={"problem": "test problem"}
        )
        # Should be 503 (service unavailable) not 500 (internal error)
        assert response.status_code in (503, 200)  # 200 if LLM is configured

    def test_solve_post_error_response_structure(self, client):
        """Test that error response has correct structure."""
        response = client.post("/solve", json={})
        # Should be a validation error with details
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_solve_post_request_validation(self, client):
        """Test that request validates against SolveRequest model."""
        # Valid request
        SolveRequest(problem="test problem")

        # Invalid requests
        with pytest.raises(ValueError):
            SolveRequest(problem="")

        with pytest.raises(ValueError):
            SolveRequest(problem="   ")


class TestRequestValidationModels:
    """Tests for Pydantic request/response models."""

    def test_solve_request_creation(self):
        """Test SolveRequest model creation."""
        req = SolveRequest(problem="test problem")
        assert req.problem == "test problem"

    def test_solve_request_rejects_empty(self):
        """Test that SolveRequest rejects empty problem."""
        with pytest.raises(ValueError):
            SolveRequest(problem="")

    def test_solve_request_rejects_whitespace(self):
        """Test that SolveRequest rejects whitespace-only problem."""
        with pytest.raises(ValueError):
            SolveRequest(problem="   ")

    def test_solve_response_creation(self):
        """Test SolveResponse model creation."""
        resp = SolveResponse(result="test result")
        assert resp.result == "test result"

    def test_health_response_creation(self):
        """Test HealthResponse model creation."""
        resp = HealthResponse(status="ok", service="test-service")
        assert resp.status == "ok"
        assert resp.service == "test-service"

    def test_index_response_creation(self):
        """Test IndexResponse model creation."""
        resp = IndexResponse(
            service="test-service",
            status="ok",
            endpoints=["GET /", "GET /health"],
            message="test message"
        )
        assert resp.service == "test-service"
        assert resp.status == "ok"


class TestErrorHandling:
    """Tests for error handling across endpoints."""

    def test_404_not_found(self, client):
        """Test that non-existent endpoints return 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test that disallowed methods return 405."""
        response = client.put("/health")
        assert response.status_code == 405

        response = client.delete("/health")
        assert response.status_code == 405

    def test_solve_post_invalid_json(self, client):
        """Test that invalid JSON returns 400."""
        response = client.post(
            "/solve",
            content="invalid json",
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 400


class TestContentNegotiation:
    """Tests for content type handling."""

    def test_responses_are_json(self, client):
        """Test that all responses are valid JSON."""
        endpoints = ["/", "/health", "/solve"]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.headers["content-type"].startswith("application/json")
            # Should not raise - response should be valid JSON
            response.json()

    def test_accepts_json_content_type(self, client):
        """Test that application/json is accepted."""
        response = client.post(
            "/solve",
            json={"problem": "test"},
            headers={"content-type": "application/json"}
        )
        # Should accept, either succeed or fail with 503, not content-type error
        assert response.status_code in (200, 503, 422)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
