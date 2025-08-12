import pandas as pd
import json
import numpy as np
from pathlib import Path

def classify_urban_rural(population_data, rural_threshold=300):
    """
    Classify population as urban or rural based on population density threshold
    """
    urban_mask = population_data >= rural_threshold
    rural_mask = population_data < rural_threshold
    
    urban_pop = population_data[urban_mask].sum()
    rural_pop = population_data[rural_mask].sum()
    
    return urban_pop, rural_pop

def process_country_data(csv_file, interval=1.0, rural_threshold=300):
    """
    Process a single country's detailed CSV file and return structured data
    """
    # Read CSV file
    df = pd.read_csv(csv_file)
    country_name = df['country'].iloc[0]
    
    # Get total population
    total_population = df['pop_density'].sum()
    
    # Create distance bins
    max_distance = df['distance'].max()
    distance_bins = np.arange(0, max_distance + interval, interval)
    
    country_data = {
        "population": int(total_population),
        "distance_intervals": {}
    }
    
    for i in range(len(distance_bins) - 1):
        bin_start = distance_bins[i]
        bin_end = distance_bins[i + 1]
        
        # Filter data for this distance bin
        mask = (df['distance'] >= bin_start) & (df['distance'] < bin_end)
        bin_data = df[mask]
        
        if len(bin_data) > 0:
            # Get population in this distance range
            bin_population = bin_data['pop_density'].sum()
            
            # Classify as urban/rural based on individual cell density
            urban_pop, rural_pop = classify_urban_rural(bin_data['pop_density'], rural_threshold)
            
            # Calculate shares
            urban_share = urban_pop / total_population if total_population > 0 else 0
            rural_share = rural_pop / total_population if total_population > 0 else 0
            
            # Create interval key (e.g., "1" for 0-1km, "2" for 1-2km)
            interval_key = str(int(bin_end))
            
            country_data["distance_intervals"][interval_key] = {
                "urban_population": int(urban_pop),
                "rural_population": int(rural_pop),
                "urban_share_of_total_population": round(urban_share, 4),
                "rural_share_of_total_population": round(rural_share, 4),
                "total_population_in_range": int(bin_population)
            }
    
    return country_data

def main():
    # Configuration
    interval = 1.0  # 1 km intervals
    rural_threshold = 300  # population density threshold for rural classification
    
    # Find all country detailed result files
    data_dir = Path("../data")
    country_files = list(data_dir.glob("result_*_detailed.csv"))
    
    print(f"Processing {len(country_files)} country detailed files...")
    
    # Process each country
    all_countries_data = {}
    
    for csv_file in country_files:
        try:
            country_name = csv_file.stem.replace("result_", "").replace("_detailed", "")
            print(f"Processing {country_name}...")
            
            country_data = process_country_data(csv_file, interval, rural_threshold)
            all_countries_data[country_name] = country_data
            
        except Exception as e:
            print(f"Error processing {csv_file.name}: {str(e)}")
            continue
    
    # Save to JSON file
    output_file = data_dir / "population_distance_analysis_fixed.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_countries_data, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to {output_file}")
    print(f"Processed {len(all_countries_data)} countries")
    
    # Print sample data for verification
    if all_countries_data:
        sample_country = list(all_countries_data.keys())[0]
        print(f"\nSample data for {sample_country}:")
        print(json.dumps(all_countries_data[sample_country], indent=2)[:500] + "...")

if __name__ == "__main__":
    main() 