def test_dashboard_stats(client):
    """Test that dashboard stats load."""
    response = client.get('/api/dashboard/stats')
    assert response.status_code == 200
    data = response.get_json()
    assert 'jobs' in data
    assert 'candidates' in data

def test_jobs_list(client):
    """Test that jobs list loads."""
    response = client.get('/api/jobs/')
    assert response.status_code == 200
    data = response.get_json()
    assert 'jobs' in data

def test_candidates_list(client):
    """Test that candidates list loads."""
    response = client.get('/api/candidates/')
    assert response.status_code == 200
    data = response.get_json()
    assert 'candidates' in data
