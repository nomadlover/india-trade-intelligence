"""
Tests for Document Analyzer and Text Extraction Engine.
"""
from student_cos.ai.doc_analyzer import DocumentAnalyzer
from student_cos.models import Priority


def test_document_extraction():
    analyzer = DocumentAnalyzer()
    syllabus_sample = """
    CS 450: Distributed Systems Syllabus
    Important: Class attendance is recommended.
    Decision: All teams agreed to use Go for RPC assignments.
    
    Deliverables and Schedule:
    - Implement Raft election timeout and heartbeat due 2026-10-25 urgent
    - Submit Project Proposal by tomorrow
    - Optional bonus: Read Chandy-Lamport snapshot paper
    """

    res = analyzer.analyze(syllabus_sample, title="Distributed Systems Syllabus")

    assert res.title == "Distributed Systems Syllabus"
    assert len(res.decisions) >= 1
    assert any("go for rpc" in d.lower() for d in res.decisions)
    assert len(res.extracted_tasks) >= 2

    # Check urgent priority extraction
    raft_task = next((t for t in res.extracted_tasks if "raft" in t.title.lower()), None)
    assert raft_task is not None
    assert raft_task.priority == Priority.HIGH
    assert raft_task.deadline == "2026-10-25"


def test_empty_document():
    analyzer = DocumentAnalyzer()
    res = analyzer.analyze("")
    assert len(res.extracted_tasks) == 0
