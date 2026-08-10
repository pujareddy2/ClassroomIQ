from typing import List, Dict, Any
from backend.app.services.curriculum_structure.structure_models import Block

def generate_statistics(blocks: List[Block]) -> Dict[str, Any]:
    stats = {
        "total_blocks": len(blocks),
        "block_types": {}
    }
    for block in blocks:
        stats["block_types"][block.block_type] = stats["block_types"].get(block.block_type, 0) + 1
    return stats
