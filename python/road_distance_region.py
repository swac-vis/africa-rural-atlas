import json
import pandas as pd
from pathlib import Path

def aggregate_by_regions():
    """Aggregate country data by regions and calculate population distribution"""
    
    # Region definitions
    regions_def = {
        "North Africa": ["Morocco", "Algeria", "Tunisia", "Libya", "Egypt", "Mauritius"],
        "West Africa": ["Senegal", "Gambia", "Guinea-Bissau", "Guinea", "Sierra Leone", 
                        "Liberia", "Côte d'Ivoire", "Ghana", "Togo", "Benin", "Nigeria", 
                        "Niger", "Burkina Faso", "Mali", "Mauritania", "Cabo Verde"],
                        # "Côte d'Ivoire" - temporarily commented out due to missing data
        "Central Africa": ["Chad", "Central African Republic", "Cameroon", "Gabon", 
                        "Congo", "Democratic Republic of the Congo", "Equatorial Guinea", 
                        "Sao Tome and Principe", "Burundi"],
                        # "Rwanda" - temporarily commented out due to missing data
        "East Africa": ["Ethiopia", "Eritrea", "Djibouti", "Somalia", "Kenya", 
                        "Uganda", "Tanzania", "Rwanda", "South Sudan", "Sudan"],
        "Southern Africa": ["South Africa", "Namibia", "Botswana", "Zimbabwe", 
                        "Zambia", "Malawi", "Mozambique", "Angola", "Lesotho", 
                        "Madagascar", "Comoros", "Swaziland", "Seychelles"]
                        # "Comoros" - temporarily commented out due to missing data
                        # "Seychelles" - temporarily commented out due to missing data
    }
    
    # Load the JSON data
    json_file = Path("../horizon/road_distance_country.json")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get all countries in the data
    available_countries = list(data.keys())
    print(f"Available countries in data: {len(available_countries)}")
    
    # Create reverse mapping from country to region
    country_to_region = {}
    for region, countries in regions_def.items():
        for country in countries:
            country_to_region[country] = region
    
    # Check which countries are not mapped
    mapped_countries = set(country_to_region.keys())
    available_countries_set = set(available_countries)
    
    unmapped_countries = available_countries_set - mapped_countries
    missing_countries = mapped_countries - available_countries_set
    
    print(f"\nUnmapped countries (in data but not in regions):")
    for country in sorted(unmapped_countries):
        print(f"  - {country}")
    
    print(f"\nMissing countries (in regions but not in data):")
    for country in sorted(missing_countries):
        print(f"  - {country}")
    
    # Aggregate data by regions
    region_data = {}
    
    for region, countries in regions_def.items():
        print(f"\nProcessing {region}...")
        region_population = 0
        region_urban_population = 0
        region_rural_population = 0
        region_distance_data = {}
        
        # Find countries in this region that exist in our data
        region_countries = [c for c in countries if c in available_countries]
        print(f"  Found {len(region_countries)} countries: {region_countries}")
        
        if not region_countries:
            print(f"  Warning: No countries found for {region}")
            continue
        
        # Calculate total population for this region (only once)
        for country in region_countries:
            country_data = data[country]
            region_population += country_data['population']
            # Add urban and rural population if available
            if 'urban_population' in country_data:
                region_urban_population += country_data['urban_population']
            if 'rural_population' in country_data:
                region_rural_population += country_data['rural_population']
        
        # Aggregate data for each distance
        for distance in range(1, 101):  # 1km to 100km
            distance_key = f"<={distance}km population"
            rural_total = 0
            urban_total = 0
            
            for country in region_countries:
                country_data = data[country]
                intervals = country_data['distance_intervals']
                
                # Sum up to this distance
                for d in range(1, distance + 1):
                    interval_key = str(d)
                    if interval_key in intervals:
                        rural_total += intervals[interval_key]['rural_population']
                        urban_total += intervals[interval_key]['urban_population']
            
            # Calculate shares
            total_at_distance = rural_total + urban_total
            share_rural = rural_total / region_population if region_population > 0 else 0
            share_urban = urban_total / region_population if region_population > 0 else 0
            
            # Calculate no access (population not within this distance)
            total_with_access = rural_total + urban_total
            total_no_access = region_population - total_with_access
            
            # Calculate rural and urban no-access separately
            rural_no_access = region_rural_population - rural_total
            urban_no_access = region_urban_population - urban_total
            
            # Calculate shares for no-access
            share_rural_no_access = rural_no_access / region_population if region_population > 0 else 0
            share_urban_no_access = urban_no_access / region_population if region_population > 0 else 0
            
            region_distance_data[distance_key] = {
                "rural": int(rural_total),
                "urban": int(urban_total),
                "total_with_access": int(total_with_access),
                "total_no_access": int(total_no_access),
                "rural_no_access": int(rural_no_access),
                "urban_no_access": int(urban_no_access),
                "share_rural": round(share_rural, 4),
                "share_urban": round(share_urban, 4),
                "share_rural_no_access": round(share_rural_no_access, 4),
                "share_urban_no_access": round(share_urban_no_access, 4),
                "share_total_with_access": round(total_with_access / region_population, 4) if region_population > 0 else 0,
                "share_total_no_access": round(total_no_access / region_population, 4) if region_population > 0 else 0
            }
        
        region_data[region] = {
            "total_population": int(region_population),
            "urban_population": int(region_urban_population),
            "rural_population": int(region_rural_population),
            **region_distance_data
        }
    
    # Save the aggregated data
    output_file = Path("../pie/road_distance_region.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(region_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to {output_file}")
    
    # Print summary
    print(f"\n=== Summary ===")
    for region, region_info in region_data.items():
        total_pop = region_info['total_population']
        urban_pop = region_info.get('urban_population', 0)
        rural_pop = region_info.get('rural_population', 0)
        
        print(f"{region}: {total_pop:,} people")
        print(f"  Urban: {urban_pop:,} ({urban_pop/total_pop:.1%})")
        print(f"  Rural: {rural_pop:,} ({rural_pop/total_pop:.1%})")
        
        # Show sample data for first few distances
        for distance in [1, 5, 10]:
            key = f"<={distance}km population"
            if key in region_info:
                data = region_info[key]
                print(f"  {distance}km: Rural {data['rural']:,} ({data['share_rural']:.1%}), "
                      f"Urban {data['urban']:,} ({data['share_urban']:.1%})")

if __name__ == "__main__":
    aggregate_by_regions() 