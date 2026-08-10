"""
Teaching Sequence Verifier component for Curriculum Coverage Intelligence Engine.
Compares intended curriculum topic sequence against actual lecture presentation sequence.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple
from app.services.coverage.coverage_models import SequenceStatus

logger = logging.getLogger(__name__)


class SequenceVerifier:
    """Verifies teaching sequence integrity and calculates sequence score."""

    @staticmethod
    def verify_sequence(
        covered_topic_order: List[Tuple[int, float]],  # [(curriculum_sequence_order, first_timestamp), ...]
        total_curriculum_topics: int,
    ) -> Tuple[Dict[int, Tuple[int, SequenceStatus]], float]:
        """
        Returns:
            (order_mapping, sequence_score_0_to_100)
            order_mapping: {curriculum_seq_order: (lecture_order_index, SequenceStatus)}
        """
        if not covered_topic_order:
            return {}, 100.0

        # Sort by actual first_timestamp in lecture
        sorted_by_lecture = sorted(covered_topic_order, key=lambda x: x[1])

        order_result: Dict[int, Tuple[int, SequenceStatus]] = {}
        inversions = 0
        skipped_prereqs = 0
        seen_curr_orders: set[int] = set()

        for lec_idx, (curr_order, t_stamp) in enumerate(sorted_by_lecture, start=1):
            status = SequenceStatus.CORRECT_SEQUENCE

            # Check if repeated
            if curr_order in seen_curr_orders:
                status = SequenceStatus.REPEATED_SEQUENCE
            seen_curr_orders.add(curr_order)

            # Check prerequisite skipping (if topic 3 is taught before topic 1 or 2)
            if curr_order > 1:
                prereqs = range(1, curr_order)
                missing_prereqs = [p for p in prereqs if p not in seen_curr_orders]
                if missing_prereqs and status == SequenceStatus.CORRECT_SEQUENCE:
                    status = SequenceStatus.SKIPPED_PREREQUISITE
                    skipped_prereqs += len(missing_prereqs)

            # Check out of order inversion
            if lec_idx > 1 and curr_order < sorted_by_lecture[lec_idx - 2][0]:
                if status == SequenceStatus.CORRECT_SEQUENCE:
                    status = SequenceStatus.OUT_OF_ORDER
                inversions += 1

            order_result[curr_order] = (lec_idx, status)

        # Compute sequence score (0-100)
        n = len(covered_topic_order)
        penalty = (inversions * 15.0) + (skipped_prereqs * 10.0)
        sequence_score = max(0.0, round(100.0 - (penalty / float(max(1, n))), 1))

        return order_result, sequence_score
