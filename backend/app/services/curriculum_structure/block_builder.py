import uuid
from typing import List, Optional
from backend.app.services.curriculum_structure.structure_models import Block, BlockType, MarkerReference

class BlockBuilder:
    @staticmethod
    def create_block(
        block_type: BlockType,
        start_line: int,
        end_line: int,
        content: str,
        marker_ref: MarkerReference,
        order: int,
        parent_id: Optional[str] = None
    ) -> Block:
        return Block(
            block_id=str(uuid.uuid4()),
            block_type=block_type,
            start_line=start_line,
            end_line=end_line,
            content=content,
            marker_ref=marker_ref,
            order=order,
            parent_id=parent_id
        )
