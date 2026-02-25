import logging
import difflib

logger = logging.getLogger(__name__)


class AmendmentDiffTracker:
    """Track and diff amendments to RFP documents."""

    def compute_diff(self, old_text: str, new_text: str) -> list[dict]:
        """Compute diff between old and new document versions."""
        differ = difflib.unified_diff(
            old_text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            lineterm='',
        )
        changes = []
        current_change = None
        for line in differ:
            if line.startswith('---') or line.startswith('+++'):
                continue
            if line.startswith('-'):
                changes.append({"type": "removed", "text": line[1:].strip()})
            elif line.startswith('+'):
                changes.append({"type": "added", "text": line[1:].strip()})
        return changes

    def assess_materiality(self, changes: list[dict]) -> bool:
        """Determine if changes are material (requiring re-review)."""
        material_keywords = [
            'shall', 'must', 'requirement', 'evaluation', 'criteria',
            'deadline', 'page limit', 'submission', 'pricing', 'cost',
        ]
        for change in changes:
            text = change.get("text", "").lower()
            if any(kw in text for kw in material_keywords):
                return True
        return False
