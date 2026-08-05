"""xai_explainability_schema

Revision ID: 999976ba9345
Revises: 1200dbbbdae5
Create Date: 2026-08-05 15:17:29.477396

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '999976ba9345'
down_revision: Union[str, Sequence[str], None] = '1200dbbbdae5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    has_table = bind.dialect.has_table(bind, 'explanation_records')

    if has_table:
        return

    op.create_table(
        'explanation_records',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('lecture_id', sa.UUID(), nullable=False),
        sa.Column('faculty_id', sa.UUID(), nullable=True),
        sa.Column('curriculum_id', sa.UUID(), nullable=True),
        sa.Column('decision_source', sa.String(length=50), nullable=False),
        sa.Column('decision_type', sa.String(length=100), nullable=False),
        sa.Column('decision_id', sa.UUID(), nullable=True),
        sa.Column('overall_confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('explanation_summary', sa.Text(), nullable=False, server_default=''),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['lecture_id'], ['lecture_sessions.id'], name=op.f('fk_explanation_records_lecture_id_lecture_sessions'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['faculty_id'], ['faculty.id'], name=op.f('fk_explanation_records_faculty_id_faculty'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['curriculum_id'], ['curricula.id'], name=op.f('fk_explanation_records_curriculum_id_curricula'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_explanation_records')),
        sa.UniqueConstraint('lecture_id', 'decision_source', 'decision_type', 'decision_id', 'status', name='uq_active_explanation_per_decision'),
    )
    op.create_index(op.f('ix_explanation_records_lecture_id'), 'explanation_records', ['lecture_id'], unique=False)
    op.create_index(op.f('ix_explanation_records_status'), 'explanation_records', ['status'], unique=False)
    op.create_index(op.f('ix_explanation_records_lecture_source'), 'explanation_records', ['lecture_id', 'decision_source'], unique=False)

    op.create_table(
        'evidence_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('explanation_record_id', sa.UUID(), nullable=False),
        sa.Column('evidence_type', sa.String(length=50), nullable=False),
        sa.Column('coverage_result_id', sa.UUID(), nullable=True),
        sa.Column('validation_result_id', sa.UUID(), nullable=True),
        sa.Column('teaching_analysis_id', sa.UUID(), nullable=True),
        sa.Column('recommendation_id', sa.UUID(), nullable=True),
        sa.Column('importance_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['explanation_record_id'], ['explanation_records.id'], name=op.f('fk_evidence_items_explanation_record_id_explanation_records'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['coverage_result_id'], ['coverage_results.id'], name=op.f('fk_evidence_items_coverage_result_id_coverage_results'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['validation_result_id'], ['validation_results.id'], name=op.f('fk_evidence_items_validation_result_id_validation_results'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['teaching_analysis_id'], ['teaching_analysis.id'], name=op.f('fk_evidence_items_teaching_analysis_id_teaching_analysis'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['recommendation_id'], ['rec_items.id'], name=op.f('fk_evidence_items_recommendation_id_rec_items'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_evidence_items')),
    )
    op.create_index(op.f('ix_evidence_items_explanation_record_id'), 'evidence_items', ['explanation_record_id'], unique=False)
    op.create_index(op.f('ix_evidence_items_coverage_result_id'), 'evidence_items', ['coverage_result_id'], unique=False)
    op.create_index(op.f('ix_evidence_items_validation_result_id'), 'evidence_items', ['validation_result_id'], unique=False)
    op.create_index(op.f('ix_evidence_items_teaching_analysis_id'), 'evidence_items', ['teaching_analysis_id'], unique=False)
    op.create_index(op.f('ix_evidence_items_recommendation_id'), 'evidence_items', ['recommendation_id'], unique=False)

    op.create_table(
        'transcript_evidence',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('evidence_item_id', sa.UUID(), nullable=False),
        sa.Column('lecture_id', sa.UUID(), nullable=False),
        sa.Column('chunk_id', sa.String(length=100), nullable=True),
        sa.Column('speaker', sa.String(length=100), nullable=False, server_default='Faculty'),
        sa.Column('snippet', sa.Text(), nullable=False),
        sa.Column('start_time', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('end_time', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['evidence_item_id'], ['evidence_items.id'], name=op.f('fk_transcript_evidence_evidence_item_id_evidence_items'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lecture_id'], ['lecture_sessions.id'], name=op.f('fk_transcript_evidence_lecture_id_lecture_sessions'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_transcript_evidence')),
        sa.UniqueConstraint('evidence_item_id', name='uq_transcript_evidence_item'),
    )
    op.create_index(op.f('ix_transcript_evidence_lecture_id'), 'transcript_evidence', ['lecture_id'], unique=False)

    op.create_table(
        'reference_citations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('evidence_item_id', sa.UUID(), nullable=False),
        sa.Column('reference_material_id', sa.UUID(), nullable=True),
        sa.Column('document_name', sa.String(length=255), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False, server_default='TEXTBOOK'),
        sa.Column('chapter', sa.String(length=255), nullable=True),
        sa.Column('section', sa.String(length=255), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('excerpt', sa.Text(), nullable=True),
        sa.Column('citation_confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['evidence_item_id'], ['evidence_items.id'], name=op.f('fk_reference_citations_evidence_item_id_evidence_items'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reference_material_id'], ['reference_materials.id'], name=op.f('fk_reference_citations_reference_material_id_reference_materials'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_reference_citations')),
        sa.UniqueConstraint('evidence_item_id', name='uq_reference_citation_item'),
    )
    op.create_index(op.f('ix_reference_citations_reference_material_id'), 'reference_citations', ['reference_material_id'], unique=False)

    op.create_table(
        'confidence_breakdowns',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('explanation_record_id', sa.UUID(), nullable=False),
        sa.Column('topic_match_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('coverage_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('validation_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('reference_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('teaching_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('recommendation_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('overall_confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['explanation_record_id'], ['explanation_records.id'], name=op.f('fk_confidence_breakdowns_explanation_record_id_explanation_records'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_confidence_breakdowns')),
        sa.UniqueConstraint('explanation_record_id', name='uq_confidence_breakdown_record'),
    )

    op.create_table(
        'reasoning_steps',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('explanation_record_id', sa.UUID(), nullable=False),
        sa.Column('step_order', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('evidence_reference', sa.String(length=200), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['explanation_record_id'], ['explanation_records.id'], name=op.f('fk_reasoning_steps_explanation_record_id_explanation_records'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_reasoning_steps')),
        sa.UniqueConstraint('explanation_record_id', 'step_order', name='uq_reasoning_step_order'),
    )
    op.create_index(op.f('ix_reasoning_steps_explanation_record_id'), 'reasoning_steps', ['explanation_record_id'], unique=False)
    op.create_index(op.f('ix_reasoning_steps_record_order'), 'reasoning_steps', ['explanation_record_id', 'step_order'], unique=False)

    op.create_table(
        'explanation_summaries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('lecture_id', sa.UUID(), nullable=False),
        sa.Column('total_explanations', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('highest_confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('lowest_confidence', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('processing_time', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['lecture_id'], ['lecture_sessions.id'], name=op.f('fk_explanation_summaries_lecture_id_lecture_sessions'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_explanation_summaries')),
        sa.UniqueConstraint('lecture_id', name='uq_explanation_summary_lecture'),
    )
    op.create_index(op.f('ix_explanation_summaries_lecture_id'), 'explanation_summaries', ['lecture_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    has_table = bind.dialect.has_table(bind, 'explanation_summaries')
    if has_table:
        op.drop_table('explanation_summaries')
    if bind.dialect.has_table(bind, 'reasoning_steps'):
        op.drop_table('reasoning_steps')
    if bind.dialect.has_table(bind, 'confidence_breakdowns'):
        op.drop_table('confidence_breakdowns')
    if bind.dialect.has_table(bind, 'reference_citations'):
        op.drop_table('reference_citations')
    if bind.dialect.has_table(bind, 'transcript_evidence'):
        op.drop_table('transcript_evidence')
    if bind.dialect.has_table(bind, 'evidence_items'):
        op.drop_table('evidence_items')
    if bind.dialect.has_table(bind, 'explanation_records'):
        op.drop_table('explanation_records')
