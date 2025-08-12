import json
import pandas as pd
from pathlib import Path

def verify_shares():
    """Verify that urban + rural shares sum to 1.0 for each country"""
    
    # Load fixed JSON data
    json_file = Path("../data/population_distance_analysis_fixed.json")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=== Share Verification ===")
    print(f"Total countries: {len(data)}")
    
    # Check each country
    issues_found = []
    total_issues = 0
    
    for country, country_data in data.items():
        total_urban_share = 0
        total_rural_share = 0
        
        # Sum all shares across distance intervals
        for interval_data in country_data['distance_intervals'].values():
            total_urban_share += interval_data['urban_share_of_total_population']
            total_rural_share += interval_data['rural_share_of_total_population']
        
        total_share = total_urban_share + total_rural_share
        
        # Check if sum equals 1.0 (with small tolerance for floating point errors)
        if abs(total_share - 1.0) > 0.001:
            issues_found.append({
                'country': country,
                'total_urban_share': total_urban_share,
                'total_rural_share': total_rural_share,
                'total_share': total_share,
                'difference': total_share - 1.0
            })
            total_issues += 1
        
        # Print first few countries for verification
        if len(issues_found) <= 5 or total_issues <= 5:
            print(f"\n{country}:")
            print(f"  Total urban share: {total_urban_share:.6f}")
            print(f"  Total rural share: {total_rural_share:.6f}")
            print(f"  Sum: {total_share:.6f}")
            print(f"  Difference from 1.0: {total_share - 1.0:.6f}")
    
    # Summary
    print(f"\n=== Summary ===")
    print(f"Countries with share sum ≠ 1.0: {total_issues}")
    
    if issues_found:
        print(f"\nCountries with issues:")
        for issue in issues_found[:10]:  # Show first 10 issues
            print(f"  {issue['country']}: {issue['total_share']:.6f} (diff: {issue['difference']:.6f})")
        
        if len(issues_found) > 10:
            print(f"  ... and {len(issues_found) - 10} more countries")
    else:
        print("✅ All countries have share sums equal to 1.0!")
    
    # Calculate average deviation
    if issues_found:
        avg_deviation = sum(abs(issue['difference']) for issue in issues_found) / len(issues_found)
        max_deviation = max(abs(issue['difference']) for issue in issues_found)
        print(f"\nAverage deviation: {avg_deviation:.6f}")
        print(f"Maximum deviation: {max_deviation:.6f}")

if __name__ == "__main__":
    verify_shares() 