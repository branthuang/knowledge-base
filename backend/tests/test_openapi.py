from app.main import app


def test_openapi_schema_generation():
    schema = app.openapi()
    assert schema is not None
    assert "paths" in schema

    paths = schema["paths"]
    # Check health endpoint
    assert "/api/health" in paths
    # Check category endpoints
    assert "/api/categories" in paths
    assert "/api/categories/tree" in paths
    assert "/api/categories/{category_id}" in paths
    # Check tag endpoints
    assert "/api/tags" in paths
    assert "/api/tags/merge" in paths
    assert "/api/tags/{tag_id}" in paths
    # Check knowledge endpoints
    assert "/api/knowledge" in paths
    assert "/api/knowledge/trash/list" in paths
    assert "/api/knowledge/{knowledge_id}" in paths
    assert "/api/knowledge/{knowledge_id}/restore" in paths
    assert "/api/knowledge/{knowledge_id}/permanent" in paths
