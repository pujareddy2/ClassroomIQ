from typing import List
from backend.app.services.curriculum_structure.structure_models import Block

def validate_blocks(blocks: List[Block]) -> List[str]:
    warnings = []
    # Check for overlapping blocks
    for i in range(len(blocks) - 1):
        if blocks[i].end_line >= blocks[i+1].start_line:
            warnings.append(f"Overlapping blocks detected: {blocks[i].block_id} and {blocks[i+1].block_id}")
    return warnings
