import requests
import os
import json
import time

API_KEY = "d7f7395fd6620e85746c0b5dadf161ed7d206bb3"

# 支持格式: "geojson", "csv", "kml"
FILE_FORMAT = "geojson"

# 非洲国家列表（联合国 54 个国家）
africa_countries = [
    "Algeria","Angola","Benin","Botswana","Burkina Faso","Burundi","Cabo Verde",
    "Cameroon","Central African Republic","Chad","Comoros","Congo","Democratic Republic of the Congo",
    "Djibouti","Egypt","Equatorial Guinea","Eritrea","Eswatini","Ethiopia","Gabon","Gambia","Ghana",
    "Guinea","Guinea-Bissau","Ivory Coast","Kenya","Lesotho","Liberia","Libya","Madagascar","Malawi",
    "Mali","Mauritania","Mauritius","Morocco","Mozambique","Namibia","Niger","Nigeria","Rwanda",
    "Sao Tome and Principe","Senegal","Seychelles","Sierra Leone","Somalia","South Africa",
    "South Sudan","Sudan","Tanzania","Togo","Tunisia","Uganda","Zambia","Zimbabwe"
]

# 创建保存目录
os.makedirs(f"africa_{FILE_FORMAT}", exist_ok=True)

def download_country_data(country, file_format):
    """下载指定国家的完整数据，支持分页"""
    print(f"Downloading {country} ...")
    
    all_features = []
    page = 1
    page_size = 100  # API默认每页100条记录
    
    while True:
        try:
            # 构建API URL，添加分页参数
            if file_format == "geojson":
                url = f"https://healthsites.io/api/v3/facilities/?api-key={API_KEY}&country={country}&output={file_format}&page={page}&page_size={page_size}"
            elif file_format in ["csv", "kml"]:
                url = f"https://healthsites.io/api/v3/facilities/?api-key={API_KEY}&country={country}&output={file_format}&page={page}&page_size={page_size}"
            elif file_format == "shapefile":
                url = f"https://healthsites.io/api/v3/shapefile/{country}?api-key={API_KEY}"
                # shapefile不支持分页，直接下载
                break
            else:
                print(f"  ❌ Unsupported format: {file_format}")
                return False
            
            print(f"  📄 Fetching page {page}...")
            response = requests.get(url, stream=True)
            
            if response.status_code == 200:
                if file_format == "geojson":
                    # 解析JSON数据
                    data = response.json()
                    if 'features' in data and data['features']:
                        features = data['features']
                        all_features.extend(features)
                        print(f"    ✅ Page {page}: {len(features)} features (Total: {len(all_features)})")
                        
                        # 如果返回的记录数少于页面大小，说明是最后一页
                        if len(features) < page_size:
                            print(f"    📊 Last page reached (got {len(features)} < {page_size})")
                            break
                        
                        # 继续获取下一页
                        page += 1
                        
                        # 添加延迟避免API限制
                        time.sleep(0.5)
                        
                    else:
                        print(f"    ⚠️ Page {page}: No features found")
                        break
                else:
                    # 对于CSV和KML，直接保存文件
                    filename = f"africa_{file_format}/{country}.{file_format}"
                    with open(filename, "wb") as f:
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:
                                f.write(chunk)
                    print(f"  ✅ Saved: {filename}")
                    return True
                
            else:
                print(f"  ❌ Failed {country} page {page}: {response.status_code}")
                if response.status_code == 404:
                    print(f"    ⚠️ No data available for {country}")
                break
                
        except Exception as e:
            print(f"  ⚠️ Error {country} page {page}: {e}")
            break
    
    # 保存合并后的GeoJSON数据
    if file_format == "geojson" and all_features:
        merged_data = {
            "type": "FeatureCollection",
            "features": all_features
        }
        
        filename = f"africa_{file_format}/{country}.{file_format}"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
        
        print(f"  🎉 Saved: {filename} ({len(all_features)} total features from {page} pages)")
        return True
    elif file_format == "geojson":
        print(f"  ❌ No data saved for {country}")
        return False
    
    return True

# 主下载循环
successful_downloads = 0
total_countries = len(africa_countries)

for i, country in enumerate(africa_countries, 1):
    print(f"\n[{i}/{total_countries}] Processing {country}")
    
    if download_country_data(country, FILE_FORMAT):
        successful_downloads += 1
    
    # 添加延迟避免API限制
    if i < total_countries:
        print("  ⏳ Waiting 2 seconds before next country...")
        time.sleep(2)

print(f"\n🎉 Download completed!")
print(f"✅ Successful: {successful_downloads}/{total_countries} countries")
print(f"❌ Failed: {total_countries - successful_downloads}/{total_countries} countries")
