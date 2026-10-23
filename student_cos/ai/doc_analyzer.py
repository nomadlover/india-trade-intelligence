"""
Document and Text Analysis Engine for Student Chief of Staff.
Extracts Tasks, Deadlines, Key Points, Decisions, and Action Items from text documents,
syllabi, lecture notes, job descriptions, or assignment briefs.
"""
from __future__ import annotations

import re
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional

from student_cos.models import DocumentAnalysisResult, ExtractedTaskItem, Priority


MONTH_NAMES = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12
}


class DocumentAnalyzer:
    """
    Deterministic rule-based and NLP extractor for notes and syllabus documents.
    """

    def analyze(self, text: str, title: str = "Document Analysis") -> DocumentAnalysisResult:
        if not text or not text.strip():
            return DocumentAnalysisResult(title=title, summary="Empty document provided.")

        lines = [line.strip() for line in text.strip().splitlines() if line.strip()]

        key_points: List[str] = []
        decisions: List[str] = []
        action_items: List[str] = []
        extracted_tasks: List[ExtractedTaskItem] = []
        extracted_deadlines: List[Dict[str, Any]] = []

        # Patterns
        decision_keywords = ["decided", "decision:", "agreed", "agreed to", "resolution:", "consensus:"]
        action_keywords = ["todo", "action item", "action:", "deliverable:", "deliverable", "task:", "[ ]", "to do:"]
        action_verbs = [
            "implement", "write", "submit", "create", "prepare", "read", "study",
            "review", "deploy", "build", "complete", "schedule", "contact", "apply"
        ]

        # Scan line by line
        for line in lines:
            lower = line.lower()
            clean_line = re.sub(r"^[-*•\d\.\s\[\]]+", "", line).strip()
            if not clean_line:
                continue

            clean_lower = clean_line.lower()
            # 1. Decisions
            if any(k in lower for k in decision_keywords):
                decisions.append(clean_line)
                continue

            # 2. Action items / tasks
            # Ignore pure category headers ending with colon like 'Deliverables and Schedule:'
            if clean_line.endswith(":") and not any(k in clean_lower for k in ["todo:", "task:", "action:"]):
                key_points.append(clean_line)
                continue

            is_action = False
            if any(k in lower for k in action_keywords):
                is_action = True
            else:
                first_word = clean_lower.split()[0] if clean_lower.split() else ""
                first_word = re.sub(r"[^\w]", "", first_word)
                if first_word in action_verbs:
                    is_action = True

            if is_action:
                action_items.append(clean_line)

                # Extract deadline if present
                dl = self._extract_date(clean_line)

                # Extract priority
                pri = Priority.MEDIUM
                if any(w in lower for w in ["urgent", "asap", "critical", "high priority", "mandatory"]):
                    pri = Priority.HIGH
                elif any(w in lower for w in ["optional", "bonus", "low priority", "if time"]):
                    pri = Priority.LOW

                # Extract time estimate
                est = self._extract_duration_minutes(clean_line)

                extracted_tasks.append(ExtractedTaskItem(
                    title=clean_line,
                    deadline=dl,
                    priority=pri,
                    estimated_minutes=est,
                    notes="Extracted from document"
                ))
                continue

            # 3. Key Points / Objectives
            if any(w in lower for w in ["note:", "important:", "overview:", "summary:", "objective:", "goal:"]) or (
                len(clean_line) > 20 and not clean_line.endswith("?")
            ):
                if len(key_points) < 8:
                    key_points.append(clean_line)

        # Standalone date scan
        for line in lines:
            dl = self._extract_date(line)
            if dl:
                extracted_deadlines.append({
                    "date": dl,
                    "context": line[:80]
                })

        summary = (
            f"Extracted {len(extracted_tasks)} actionable tasks, {len(decisions)} decisions, "
            f"and {len(key_points)} key conceptual points."
        )

        return DocumentAnalysisResult(
            title=title,
            summary=summary,
            key_points=key_points,
            decisions=decisions,
            action_items=action_items,
            extracted_tasks=extracted_tasks,
            extracted_deadlines=extracted_deadlines
        )

    def _extract_date(self, text: str) -> Optional[str]:
        """Extract ISO date YYYY-MM-DD from various human date formats."""
        # 1. Check ISO format 2026-10-25
        iso_match = re.search(r"\b(20\d{2})[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])\b", text)
        if iso_match:
            return f"{iso_match.group(1)}-{iso_match.group(2)}-{iso_match.group(3)}"

        # 2. Check "Oct 25" or "October 25, 2026"
        month_match = re.search(
            r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s*,?\s*(20\d{2}))?\b",
            text,
            re.IGNORECASE
        )
        if month_match:
            m_str = month_match.group(1).lower()
            month_num = MONTH_NAMES.get(m_str, 1)
            day_num = int(month_match.group(2))
            year = int(month_match.group(3)) if month_match.group(3) else date.today().year
            try:
                parsed_d = date(year, month_num, day_num)
                # If date is in the past by > 6 months and no year was specified, assume next year
                if not month_match.group(3) and parsed_d < date.today() - timedelta(days=60):
                    parsed_d = date(year + 1, month_num, day_num)
                return parsed_d.isoformat()
            except Exception:
                pass

        # 3. Relative dates
        text_lower = text.lower()
        today = date.today()
        if "today" in text_lower:
            return today.isoformat()
        if "tomorrow" in text_lower:
            return (today + timedelta(days=1)).isoformat()
        if "in 2 days" in text_lower:
            return (today + timedelta(days=2)).isoformat()
        if "in 3 days" in text_lower:
            return (today + timedelta(days=3)).isoformat()
        if "in a week" in text_lower or "in 1 week" in text_lower:
            return (today + timedelta(days=7)).isoformat()

        return None

    def _extract_duration_minutes(self, text: str) -> int:
        """Extract estimated minutes from duration expressions."""
        lower = text.lower()
        hr_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h)\b", lower)
        if hr_match:
            return int(float(hr_match.group(1)) * 60)

        min_match = re.search(r"(\d+)\s*(?:minutes?|mins?|m)\b", lower)
        if min_match:
            return int(min_match.group(1))

        return 45  # Default estimated minutes
