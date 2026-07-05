from src.hadocs.project.quality import ProjectQuality


def test_project_quality_score():
    q = ProjectQuality(True, True, True, True, True)
    assert q.score == 100
    assert q.release_ready is True
