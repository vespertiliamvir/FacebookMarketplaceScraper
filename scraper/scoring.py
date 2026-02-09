"""
Scoring Engine module.

Assigns a quality score (0-100) to listings based on price, seller profile, and description keywords.
"""

import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Scoring Weights
SCORE_WEIGHTS = {
    'base_score': 50,
    'price_deal_ratio': 20,  # Max points for good price
    'seller_type': {
        'Likely Private': 10,
        'Unknown': 0,
        'Possible Flipper': -10,
        'Dealer/Business': -15
    },
    'green_flag': 3,   # Points per green flag
    'red_flag': -10,   # Points per red flag
    'dealer_keyword': -5 # Points for finding dealer keywords in description
}

# Keywords indicating a good private seller or well-maintained car
GREEN_FLAGS = [
    r'garage kept',
    r'service records',
    r'maintenance records',
    r'one owner',
    r'1 owner',
    r'single owner',
    r'clean title',
    r'title in hand',
    r'elderly owned',
    r'highway miles',
    r'new tires',
    r'fresh oil',
    r'adult owned',
    r'well maintained',
    r'runs great',
    r'drives great',
    r'must see',
    r'cash only',
    r'no trades'
]

# Keywords indicating potential issues or junk cars
RED_FLAGS = [
    r'rebuilt',
    r'salvage',
    r'mechanic special',
    r'mechanics special',
    r'needs work',
    r'parts only',
    r'parting out',
    r'no title',
    r'bill of sale',
    r'lost title',
    r'misfire',
    r'leak',
    r'knocking',
    r'overheats',
    r'transmission slip',
    r'blown head',
    r'rough idle',
    r'bring trailer',
    r'tow away',
    r'as is'
]

# Keywords that suggest a dealer/flipper even if not explicitly marked
DEALER_KEYWORDS = [
    r'financing',
    r'finance available',
    r'down payment',
    r'monthly payment',
    r'bad credit',
    r'all credit',
    r'buy here pay here',
    r'bhph',
    r'se habla',
    r'www\.',
    r'\.com',
    r'llc',
    r'motors',
    r'auto sales',
    r'inventory',
    r'dealership',
    r'doc fee',
    r'dealer fee',
    r'\+\s*tax',
    r'call for price'
]

class ScoringEngine:
    """
    Analyzes listing data to generate a 'Deal Score'.
    """
    
    def __init__(self):
        self.green_patterns = [re.compile(p, re.IGNORECASE) for p in GREEN_FLAGS]
        self.red_patterns = [re.compile(p, re.IGNORECASE) for p in RED_FLAGS]
        self.dealer_patterns = [re.compile(p, re.IGNORECASE) for p in DEALER_KEYWORDS]

    def calculate_score(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate score for a single listing.
        
        Returns:
            Dictionary with 'score', 'green_flags', 'red_flags', 'notes'
        """
        score = SCORE_WEIGHTS['base_score']
        notes = []
        found_green = []
        found_red = []
        
        description = listing.get('description', '') or ''
        title = listing.get('title', '') or ''
        full_text = f"{title} {description}"
        
        # 1. Price Score (Deal Ratio)
        # Ratio 1.0 = Fair. >1.2 = Good. <0.8 = Bad.
        deal_ratio = listing.get('deal_ratio')
        if deal_ratio:
            # Normalize: 1.0 -> 0 pts. 1.5 -> +20 pts. 0.5 -> -20 pts.
            # Formula: (Ratio - 1.0) * 40
            price_points = int((deal_ratio - 1.0) * 40)
            # Cap at +/- 20
            price_points = max(min(price_points, 20), -20)
            score += price_points
            if price_points > 0:
                notes.append(f"Good Price (+{price_points})")
        
        # 2. Seller Type Score
        seller_type = listing.get('seller_type', 'Unknown')
        seller_points = SCORE_WEIGHTS['seller_type'].get(seller_type, 0)
        score += seller_points
        if seller_points != 0:
            notes.append(f"Seller: {seller_type} ({seller_points:+})")
            
        # 3. Dealer Keyword Detection (if not already marked as dealer)
        is_business = listing.get('is_business', False)
        if not is_business and seller_type != 'Dealer/Business':
            dealer_hits = [p.pattern for p in self.dealer_patterns if p.search(full_text)]
            if dealer_hits:
                score += SCORE_WEIGHTS['dealer_keyword']
                notes.append(f"Dealer Keywords Found ({SCORE_WEIGHTS['dealer_keyword']})")
                listing['seller_type'] = 'Suspected Dealer' # Update type hint
        
        # 4. Description Analysis (Green/Red Flags)
        for pattern in self.green_patterns:
            if pattern.search(full_text):
                found_green.append(pattern.pattern.replace(r'\\', ''))
                score += SCORE_WEIGHTS['green_flag']
        
        for pattern in self.red_patterns:
            if pattern.search(full_text):
                found_red.append(pattern.pattern.replace(r'\\', ''))
                score += SCORE_WEIGHTS['red_flag']
                
        # Clamp score 0-100
        score = max(0, min(100, score))
        
        return {
            'score': score,
            'green_flags': found_green,
            'red_flags': found_red,
            'notes': notes
        }
