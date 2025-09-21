#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复失败的4个国家数据下载
直接下载JSON格式的健康设施数据，支持完整分页
"""

import requests
import json
import os
import time

API_KEY = "d7f7395fd6620e85746c0b5dadf161ed7d206bb3"

# 失败的4个国家及其可能的名称变体
failed_countries = {
    "Cabo Verde": [
        "Cabo Verde",
        "Cape Verde", 
        "Cape Verde Islands",
        "CV",
        "cabo-verde"
    ],
    "Congo": [
        "Congo",
        "Republic of Congo",
        "Republic of the Congo",
        "Congo Republic",
        "Congo-Brazzaville",
        "Congo Brazzaville",
        "Brazzaville Congo",
        "Congo Republic (Brazzaville)",
        "Republic of the Congo (Brazzaville)",
        "République du Congo",
        "Republique du Congo",
        "Congo-Brazzaville Republic",
        "CG",
        "congo",
        "congo-brazzaville",
        "congo_brazzaville"
    ],
    "Gambia": [
        "Gambia",
        "The Gambia",
        "Gambia, The",
        "GM",
        "gambia"
    ],
    "Sao Tome and Principe": [
        "Sao Tome and Principe",
        "São Tomé and Príncipe",
        "Sao Tome & Principe",
        "ST",
        "sao-tome-and-principe",
        "sao-tome"
    ]
}

def download_country_complete_data(country_name, api_key):
    """下载指定国家的完整数据，支持分页"""
    print(f"    开始下载完整数据...")
    
    all_features = []
    page = 1
    page_size = 100  # API默认每页100条记录
    
    while True:
        try:
            # 构建API URL，添加分页参数
            url = f"https://healthsites.io/api/v3/facilities/?api-key={api_key}&country={country_name}&output=geojson&page={page}&page_size={page_size}"
            
            print(f"      📄 获取第 {page} 页...")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                # 检查返回的内容类型
                content_type = response.headers.get('content-type', '')
                
                if 'application/json' in content_type or response.text.strip().startswith('{'):
                    try:
                        # 尝试解析JSON
                        data = response.json()
                        if 'features' in data and data['features']:
                            features = data['features']
                            all_features.extend(features)
                            print(f"        ✅ 第 {page} 页: {len(features)} 个设施 (总计: {len(all_features)})")
                            
                            # 如果返回的记录数少于页面大小，说明是最后一页
                            if len(features) < page_size:
                                print(f"        📊 最后一页 (获取 {len(features)} < {page_size})")
                                break
                            
                            # 继续获取下一页
                            page += 1
                            
                            # 添加延迟避免API限制
                            time.sleep(0.5)
                            
                        else:
                            print(f"        ⚠️ 第 {page} 页: 没有设施数据")
                            break
                            
                    except json.JSONDecodeError:
                        print(f"        ❌ 第 {page} 页: 返回的不是有效JSON")
                        break
                else:
                    print(f"        ❌ 第 {page} 页: 返回的不是JSON格式")
                    break
            else:
                print(f"        ❌ 第 {page} 页: HTTP {response.status_code}")
                break
                
        except Exception as e:
            print(f"        ❌ 第 {page} 页: 请求错误: {e}")
            break
    
    if all_features:
        # 创建完整的GeoJSON数据
        complete_data = {
            "type": "FeatureCollection",
            "features": all_features
        }
        return 200, complete_data, len(all_features), page
    else:
        return None, None, 0, 0

def try_download_country_json(country_name, api_key):
    """尝试下载指定国家的JSON数据（保持向后兼容）"""
    # 使用正确的API端点
    url = f"https://healthsites.io/api/v3/facilities/?api-key={api_key}&country={country_name}&output=geojson"
    
    try:
        print(f"    尝试URL: {url}")
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            # 检查返回的内容类型
            content_type = response.headers.get('content-type', '')
            
            if 'application/json' in content_type or response.text.strip().startswith('{'):
                try:
                    # 尝试解析JSON
                    data = response.json()
                    if 'features' in data or 'type' in data:
                        facility_count = len(data.get('features', []))
                        return 200, data, facility_count, 1
                    else:
                        print(f"      ⚠️ 返回的不是GeoJSON格式")
                except json.JSONDecodeError:
                    print(f"      ⚠️ 返回的不是有效JSON")
            else:
                print(f"      ⚠️ 返回的不是JSON格式")
        else:
            print(f"      ❌ HTTP {response.status_code}")
            
    except Exception as e:
        print(f"      ❌ 请求错误: {e}")
    
    return None, None, 0, 0

def main():
    print("🔧 尝试修复失败的4个国家数据下载...")
    print("📊 现在支持完整分页数据获取！")
    print("=" * 60)
    
    # 创建目录
    os.makedirs("africa_geojson", exist_ok=True)
    
    success_count = 0
    
    for original_name, name_variants in failed_countries.items():
        print(f"\n🌍 尝试修复: {original_name}")
        print("-" * 40)
        
        success = False
        for variant in name_variants:
            print(f"  尝试名称: '{variant}'")
            
            # 首先尝试完整分页下载
            status_code, data, facility_count, total_pages = download_country_complete_data(variant, API_KEY)
            
            if status_code == 200 and data:
                # 保存数据
                filename = f"africa_geojson/{original_name}.geojson"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                print(f"  ✅ 成功! 使用名称: '{variant}'")
                print(f"  💾 保存到: {filename}")
                print(f"  📊 包含 {facility_count} 个健康设施 (来自 {total_pages} 页)")
                
                success = True
                success_count += 1
                break
            else:
                print(f"    ❌ 完整分页下载失败，尝试单页下载...")
                
                # 如果完整分页失败，尝试单页下载（向后兼容）
                status_code, data, facility_count, total_pages = try_download_country_json(variant, API_KEY)
                
                if status_code == 200 and data:
                    # 保存数据
                    filename = f"africa_geojson/{original_name}.geojson"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    print(f"  ✅ 成功! 使用名称: '{variant}' (单页模式)")
                    print(f"  💾 保存到: {filename}")
                    print(f"  📊 包含 {facility_count} 个健康设施")
                    
                    success = True
                    success_count += 1
                    break
                else:
                    print(f"    ❌ 单页下载也失败了")
        
        if not success:
            print(f"  ⚠️ 所有名称变体都失败了")
    
    print("\n" + "=" * 60)
    print(f"🎯 修复结果: {success_count}/{len(failed_countries)} 个国家成功")
    
    if success_count > 0:
        print("\n✅ 成功修复的国家:")
        for original_name, name_variants in failed_countries.items():
            filename = f"africa_geojson/{original_name}.geojson"
            if os.path.exists(filename):
                # 显示文件大小和设施数量
                file_size = os.path.getsize(filename)
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        facility_count = len(data.get('features', []))
                    print(f"  - {original_name}: {facility_count} 个设施 ({file_size:,} 字节)")
                except:
                    print(f"  - {original_name}: 文件已保存")
        
        print(f"\n💡 建议: 更新原始下载脚本中的国家名称")
    
    # 显示API文档链接
    print(f"\n📚 如果仍有问题，可以查看API文档:")
    print(f"   https://healthsites.io/api/docs")
    print(f"   或联系API支持获取正确的国家名称格式")

if __name__ == "__main__":
    main()
