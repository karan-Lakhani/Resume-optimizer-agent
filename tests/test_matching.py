import pytest
from pydantic import ValidationError

from src.common.schemas import JobMatchResult


def test_job_match_result_valid():
    result = JobMatchResult(
        match_score=82,
        matched_skills=["Python", "SQL"],
        missing_skills=["Kubernetes"],
        summary="Strong fit — candidate has direct experience in data engineering.",
    )
    assert result.match_score == 82
    assert "Python" in result.matched_skills
    assert "Kubernetes" in result.missing_skills


def test_job_match_result_empty_skills():
    result = JobMatchResult(
        match_score=30,
        matched_skills=[],
        missing_skills=[],
        summary="Weak fit.",
    )
    assert result.matched_skills == []
    assert result.missing_skills == []


def test_job_match_result_requires_match_score():
    with pytest.raises(ValidationError):
        JobMatchResult(
            matched_skills=["Python"],
            missing_skills=[],
            summary="Missing score.",
        )


def test_job_match_result_requires_summary():
    with pytest.raises(ValidationError):
        JobMatchResult(
            match_score=50,
            matched_skills=[],
            missing_skills=[],
        )


def test_job_match_result_requires_matched_skills():
    with pytest.raises(ValidationError):
        JobMatchResult(
            match_score=50,
            missing_skills=[],
            summary="Missing matched_skills field.",
        )


def test_job_match_result_requires_missing_skills():
    with pytest.raises(ValidationError):
        JobMatchResult(
            match_score=50,
            matched_skills=[],
            summary="Missing missing_skills field.",
        )


def test_job_match_score_boundary_values():
    low = JobMatchResult(match_score=0, matched_skills=[], missing_skills=[], summary="No fit.")
    high = JobMatchResult(match_score=100, matched_skills=["Python"], missing_skills=[], summary="Perfect fit.")
    assert low.match_score == 0
    assert high.match_score == 100
