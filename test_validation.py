"""
Validation test script - Tests imports and basic functionality without scraping.
"""

import sys
import traceback

def test_imports():
    """Test all module imports."""
    print("Testing imports...")
    errors = []
    
    try:
        from scraper import config
        print("  ✓ config")
    except Exception as e:
        errors.append(f"config: {e}")
    
    try:
        from scraper import utils
        print("  ✓ utils")
    except Exception as e:
        errors.append(f"utils: {e}")
    
    try:
        from scraper import preferences
        print("  ✓ preferences")
    except Exception as e:
        errors.append(f"preferences: {e}")
    
    try:
        from scraper import facebook_scraper
        print("  ✓ facebook_scraper")
    except Exception as e:
        errors.append(f"facebook_scraper: {e}")
    
    try:
        from scraper import price_comparator
        print("  ✓ price_comparator")
    except Exception as e:
        errors.append(f"price_comparator: {e}")
    
    try:
        from scraper import data_processor
        print("  ✓ data_processor")
    except Exception as e:
        errors.append(f"data_processor: {e}")
    
    try:
        from scraper import csv_exporter
        print("  ✓ csv_exporter")
    except Exception as e:
        errors.append(f"csv_exporter: {e}")
    
    return errors

def test_utils():
    """Test utility functions."""
    print("\nTesting utility functions...")
    from scraper.utils import clean_price, clean_mileage, parse_car_title, calculate_deal_ratio
    
    errors = []
    
    # Test clean_price
    tests = [
        ("$12,500", 12500.0),
        ("$12.5k", 12500.0),
        ("12500", 12500.0),
    ]
    
    for input_val, expected in tests:
        result = clean_price(input_val)
        if result == expected:
            print(f"  ✓ clean_price('{input_val}') = {result}")
        else:
            errors.append(f"clean_price('{input_val}'): expected {expected}, got {result}")
    
    # Test clean_mileage
    tests = [
        ("50k miles", 50000),
        ("50,000 mi", 50000),
        ("50000", 50000),
    ]
    
    for input_val, expected in tests:
        result = clean_mileage(input_val)
        if result == expected:
            print(f"  ✓ clean_mileage('{input_val}') = {result}")
        else:
            errors.append(f"clean_mileage('{input_val}'): expected {expected}, got {result}")
    
    # Test parse_car_title
    result = parse_car_title("2015 Honda Civic LX")
    if result['year'] == '2015' and result['make'] == 'Honda' and result['model'] == 'Civic':
        print(f"  ✓ parse_car_title('2015 Honda Civic LX') = {result}")
    else:
        errors.append(f"parse_car_title failed: {result}")
    
    # Test calculate_deal_ratio
    result = calculate_deal_ratio(10000, 12000)
    if result == 1.2:
        print(f"  ✓ calculate_deal_ratio(10000, 12000) = {result}")
    else:
        errors.append(f"calculate_deal_ratio: expected 1.2, got {result}")
    
    return errors

def test_data_processor():
    """Test data processor with mock data."""
    print("\nTesting data processor...")
    from scraper.data_processor import DataProcessor
    
    errors = []
    
    # Mock listings
    listings = [
        {
            'title': '2015 Honda Civic',
            'price': 10000,
            'description': 'Great car',
            'mileage': 50000,
            'images': ['url1', 'url2'],
            'listing_url': 'https://facebook.com/test',
            'fair_market_price': 12000,
        },
        {
            'title': '2018 Toyota Camry',
            'price': 15000,
            'description': 'Excellent condition',
            'mileage': 30000,
            'images': ['url3'],
            'listing_url': 'https://facebook.com/test2',
            'fair_market_price': 16000,
        },
    ]
    
    processor = DataProcessor()
    processed = processor.process(listings)
    
    if len(processed) == 2:
        print(f"  ✓ Processed {len(processed)} listings")
    else:
        errors.append(f"Expected 2 listings, got {len(processed)}")
    
    # Check deal ratios calculated
    if processed[0].get('deal_ratio') is not None:
        print(f"  ✓ Deal ratios calculated")
    else:
        errors.append("Deal ratios not calculated")
    
    # Check sorting (best deal first)
    if processed[0]['deal_ratio'] >= processed[1]['deal_ratio']:
        print(f"  ✓ Listings sorted correctly")
    else:
        errors.append("Listings not sorted correctly")
    
    return errors

def test_csv_exporter():
    """Test CSV exporter with mock data."""
    print("\nTesting CSV exporter...")
    from scraper.csv_exporter import CSVExporter
    import os
    
    errors = []
    
    # Mock listings
    listings = [
        {
            'title': '2015 Honda Civic',
            'price': 10000,
            'description': 'Great car',
            'mileage': 50000,
            'images': ['url1', 'url2'],
            'listing_url': 'https://facebook.com/test',
            'fair_market_price': 12000,
            'deal_ratio': 1.2,
            'year': '2015',
            'make': 'Honda',
            'model': 'Civic',
        },
    ]
    
    exporter = CSVExporter()
    output_file = exporter.export(listings, 'test_output.csv')
    
    if output_file and os.path.exists(output_file):
        print(f"  ✓ CSV file created: {output_file}")
        # Clean up
        os.remove(output_file)
        print(f"  ✓ Test file cleaned up")
    else:
        errors.append("CSV file not created")
    
    return errors

def main():
    """Run all validation tests."""
    print("="*70)
    print("VALIDATION TEST SUITE")
    print("="*70)
    
    all_errors = []
    
    # Test imports
    errors = test_imports()
    all_errors.extend(errors)
    
    if not errors:
        # Test utils
        errors = test_utils()
        all_errors.extend(errors)
        
        # Test data processor
        errors = test_data_processor()
        all_errors.extend(errors)
        
        # Test CSV exporter
        errors = test_csv_exporter()
        all_errors.extend(errors)
    
    # Summary
    print("\n" + "="*70)
    if all_errors:
        print("VALIDATION FAILED")
        print("="*70)
        print("\nErrors found:")
        for error in all_errors:
            print(f"  ✗ {error}")
        return 1
    else:
        print("✓ ALL VALIDATION TESTS PASSED")
        print("="*70)
        print("\nAll modules imported successfully!")
        print("All utility functions working correctly!")
        print("Data processing works as expected!")
        print("CSV export works as expected!")
        print("\nThe scraper is ready to use!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
