
import sys
import os
import unittest
import pandas as pd
import shutil
from datetime import datetime

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from scraper.csv_exporter import CSVExporter
from scraper.config import OUTPUT_SETTINGS

class TestCSVExport(unittest.TestCase):
    def setUp(self):
        self.exporter = CSVExporter()
        self.test_file = f"test_export_{int(datetime.now().timestamp())}.csv"
        
    def tearDown(self):
        if os.path.exists(self.test_file):
            try:
                os.remove(self.test_file)
            except:
                pass

    def test_export_columns(self):
        """Verify that the exported CSV contains all expected columns including new Scoring fields."""
        
        # Create dummy processed listings
        listings = [
            {
                'title': '2015 Honda Civic',
                'price': 10000,
                'description': 'Great car',
                'mileage': 50000,
                'images': ['http://example.com/img.jpg'],
                'listing_url': 'http://facebook.com/item/123',
                'fair_market_price': 12000,
                'deal_ratio': 1.2,
                'year': '2015',
                'make': 'Honda',
                'model': 'Civic',
                'seller_type': 'Private',
                'profile_age': 'N/A',
                'is_business': False,
                'seller_rating': 'N/A',
                # New fields
                'score': 85,
                'green_flags': 'garage kept, one owner',
                'red_flags': '',
                'notes': 'Good Price (+20)'
            }
        ]
        
        # Export
        output_path = self.exporter.export(listings, self.test_file)
        
        # Read back
        df = pd.read_csv(output_path)
        
        # Check columns
        expected_columns = OUTPUT_SETTINGS['columns']
        missing_columns = [col for col in expected_columns if col not in df.columns]
        
        if missing_columns:
            print(f"\n[X] Missing columns: {missing_columns}")
        else:
            print("\n[+] All columns present.")
            
        self.assertEqual(len(missing_columns), 0, f"Missing columns in CSV: {missing_columns}")
        
        # Check values
        row = df.iloc[0]
        self.assertEqual(row['Score'], 85)
        self.assertEqual(row['Green_Flags'], 'garage kept, one owner')
        print(f"[+] Score value verified: {row['Score']}")

if __name__ == '__main__':
    unittest.main()
