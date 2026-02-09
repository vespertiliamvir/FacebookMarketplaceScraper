
import sys
import os
import unittest
from typing import Dict, Any

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from scraper.scoring import ScoringEngine

class TestScoringEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ScoringEngine()

    def test_perfect_private_listing(self):
        """Test a 'unicorn' listing: private seller, good price, great keywords."""
        listing = {
            'title': '2015 Honda Civic EX',
            'description': 'One owner, garage kept, service records available. Clean title in hand. Highway miles.',
            'price': 10000,
            'fair_market_price': 12000, # Deal ratio 1.2 (+20 pts max)
            'seller_type': 'Likely Private', # +10
            'is_business': False
        }
        # Calc deal ratio manually for input
        listing['deal_ratio'] = listing['fair_market_price'] / listing['price']
        
        result = self.engine.calculate_score(listing)
        
        print(f"\n[+] Perfect Listing Score: {result['score']}")
        print(f"   Notes: {result['notes']}")
        print(f"   Green Flags: {result['green_flags']}")
        
        # Base 50 + 20 (price) + 10 (private) + 3*4 (keywords) = ~92
        self.assertGreater(result['score'], 80)
        self.assertIn('one owner', result['green_flags'])
        self.assertIn('garage kept', result['green_flags'])

    def test_junk_listing(self):
        """Test a bad listing: salvage title, mechanical issues."""
        listing = {
            'title': '2010 Ford Focus',
            'description': 'Rebuilt title, runs rough, needs work. Misfire on cylinder 4. As is.',
            'price': 3000,
            'fair_market_price': 3000, # Ratio 1.0 (0 pts)
            'seller_type': 'Unknown', # 0 pts
            'is_business': False
        }
        listing['deal_ratio'] = 1.0
        
        result = self.engine.calculate_score(listing)
        
        print(f"\n[-] Junk Listing Score: {result['score']}")
        print(f"   Notes: {result['notes']}")
        print(f"   Red Flags: {result['red_flags']}")
        
        # Base 50 - 10*4 (red flags) = 10 -> clamped 0-100
        self.assertLess(result['score'], 30)
        self.assertIn('rebuilt', result['red_flags'])
        self.assertIn('needs work', result['red_flags'])

    def test_hidden_dealer(self):
        """Test a dealer masquerading as private but with keywords."""
        listing = {
            'title': '2018 Chevy Malibu',
            'description': 'Financing available, bad credit ok. Call for price. www.bestcars.com',
            'price': 15000,
            'fair_market_price': 14000, # Ratio 0.93 (-pts)
            'seller_type': 'Unknown', # 0 pts initially
            'is_business': False
        }
        listing['deal_ratio'] = 0.93
        
        result = self.engine.calculate_score(listing)
        
        print(f"\n[!] Hidden Dealer Score: {result['score']}")
        print(f"   Notes: {result['notes']}")
        
        # Should detect dealer keywords
        self.assertIn('Dealer Keywords Found', str(result['notes']))
        # Base 50 - pts for ratio - 5 (dealer keyword)
        self.assertLess(result['score'], 50)

if __name__ == '__main__':
    unittest.main()
