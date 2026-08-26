# Database Verification Guide

Run these against the PostgreSQL database after each write request, replacing UUID placeholders. They verify persisted records rather than request-memory output.

```sql
-- Authentication
SELECT id, email, role, is_active, created_at FROM users WHERE email = :email;

-- Curriculum upload
SELECT id, title, processing_status, file_path, created_at FROM curricula WHERE id = :curriculum_id;
SELECT id, topic_name, node_type, parent_topic_id FROM topics WHERE curriculum_id = :curriculum_id ORDER BY display_order;

-- Reference upload
SELECT id, title, document_type, processing_status, file_path FROM reference_materials WHERE id = :reference_id;
SELECT id, topic_id, reference_material_id FROM topic_references WHERE reference_material_id = :reference_id;

-- Transcript upload
SELECT id, lecture_id, processed_at FROM transcripts WHERE lecture_id = :lecture_id;
SELECT tc.id, tc.transcript_id, tc.start_time, tc.end_time, tc.text FROM transcript_chunks tc JOIN transcripts t ON t.id = tc.transcript_id WHERE t.lecture_id = :lecture_id ORDER BY tc.start_time;
SELECT id, chunk_id, topic_id, confidence_score FROM transcript_topic_mappings WHERE lecture_id = :lecture_id;

-- Technical validation
SELECT id, lecture_id, overall_validation_score, lecture_quality FROM validation_summaries WHERE lecture_id = :lecture_id;
SELECT id, lecture_id, validation_status, category FROM validation_results WHERE lecture_id = :lecture_id;
SELECT id, validation_result_id FROM validation_evidence WHERE lecture_id = :lecture_id;

-- Curriculum coverage
SELECT id, lecture_id, weighted_coverage_percentage FROM coverage_summaries WHERE lecture_id = :lecture_id;
SELECT id, lecture_id, topic_id, coverage_status FROM coverage_details WHERE lecture_id = :lecture_id;
SELECT id, lecture_id, start_time, end_time FROM coverage_timelines WHERE lecture_id = :lecture_id;

-- Teaching intelligence
SELECT * FROM teaching_analysis WHERE lecture_id = :lecture_id;
SELECT * FROM teaching_summary WHERE lecture_id = :lecture_id;

-- Recommendations
SELECT id, lecture_id, faculty_id, total_recommendations, is_active FROM rec_analyses WHERE lecture_id = :lecture_id;
SELECT id, lecture_id, priority_level, priority_score, status FROM rec_items WHERE lecture_id = :lecture_id;

-- Explainable AI
SELECT * FROM explanation_records WHERE lecture_id = :lecture_id;
SELECT * FROM evidence_items WHERE explanation_id IN (SELECT id FROM explanation_records WHERE lecture_id = :lecture_id);
SELECT * FROM explanation_summaries WHERE lecture_id = :lecture_id;
```

For every POST, record the returned resource or lecture ID, run the matching query in a new `psql` session, then GET the API resource and compare the persisted fields. A GET must be repeated after restarting the API process to demonstrate it is reading PostgreSQL rather than retained process state.

For performance verification, run `EXPLAIN (ANALYZE, BUFFERS)` on the filtered `lecture_id`, `curriculum_id`, and `faculty_id` queries above. Add an index before launch if any expected production query performs a sequential scan at the projected data volume.
