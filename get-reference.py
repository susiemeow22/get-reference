import os
import json
import time
from Bio import Entrez, Medline
from openai import OpenAI

# --- 配置 ---
Entrez.email = "medical_app@test.com"
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

# 定义版块及关键词
CATEGORIES = {
    "肺纤维化": '"Pulmonary Fibrosis"[Title/Abstract]',
    "支气管镜": '("Bronchoscopy"[Title/Abstract] OR "Interventional Pulmonology"[Title/Abstract])',
    "结节病": '"Sarcoidosis"[Title/Abstract]',
    "ILD": '("Interstitial Lung Disease"[Title/Abstract] NOT "Pulmonary Fibrosis"[Title/Abstract])'
}

def get_summary(client, title, abstract):
    if not abstract: return "摘要缺失。"
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个呼吸医学专家，请用中文一句话概括文献结论，40字内。直接说结论。"},
                {"role": "user", "content": f"标题: {title}\n摘要: {abstract[:1200]}"}
            ]
        )
        return response.choices[0].message.content
    except:
        return "AI 总结暂时不可用。"

def fetch_category(client, category_name, query):
    print(f"🔎 正在检索版块: {category_name}...")
    full_query = f'{query} AND ("last 30 days"[DP])'
    handle = Entrez.esearch(db="pubmed", term=full_query, retmax=20, sort="relevance")
    record = Entrez.read(handle)
    handle.close()
    
    ids = record.get("IdList", [])
    if not ids: return []

    fetch_handle = Entrez.efetch(db="pubmed", id=ids, rettype="medline", retmode="text")
    records = list(Medline.parse(fetch_handle))
    fetch_handle.close()

    results = []
    for r in records:
        title = r.get("TI", "No Title")
        print(f"  📝 总结: {title[:30]}...")
        summary = get_summary(client, title, r.get("AB", ""))
        
        results.append({
            "title": title,
            "journal": r.get("TA", "Unknown"),
            "date": r.get("DP", "No Date"),
            "authors": ", ".join(r.get("AU", [])),
            "link": f"https://pubmed.ncbi.nlm.nih.gov/{r.get('PMID')}/",
            "summary": summary
        })
        time.sleep(0.5) # DeepSeek 很快，微小延迟即可
    return results

def main():
    if not DEEPSEEK_API_KEY: return
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    
    all_data = {}
    for name, query in CATEGORIES.items():
        all_data[name] = fetch_category(client, name, query)
    
    os.makedirs('docs', exist_ok=True)
    with open('docs/data.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
    print("✅ 所有版块更新完成！")

if __name__ == "__main__":
    main()
