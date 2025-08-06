def test_read_root(page_client):
    response = page_client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "</html>" in response.text
