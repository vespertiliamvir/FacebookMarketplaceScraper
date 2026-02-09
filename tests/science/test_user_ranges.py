
from typing import List, Tuple

def _generate_price_ranges(min_p: int, max_p: int, chunks: int) -> List[Tuple[int, int]]:
    if max_p <= min_p:
        return [(min_p, max_p)]
        
    total_range = max_p - min_p
    step = total_range // chunks
    
    ranges = []
    current_min = min_p
    
    for i in range(chunks):
        current_max = current_min + step
        if i == chunks - 1:
            current_max = max_p # Ensure last chunk hits the max
        
        ranges.append((current_min, current_max))
        current_min = current_max + 1
        
    return ranges

print("Testing user scenario (2900-3000, 4 workers):")
ranges = _generate_price_ranges(2900, 3000, 4)
for i, r in enumerate(ranges):
    print(f"Chunk {i+1}: {r}")

print(f"Total chunks: {len(ranges)}")
