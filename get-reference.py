import os
import json
import time
from Bio import Entrez, Medline
import google.generativeai as genai

# --- 1. 配置 ---
Entrez.email = "medical_app@test.com"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def main():
    print("🚀 程序启动...")
    if not GEMINI_API_KEY:
        print("❌ 未发现 API KEY")
        return

    genai.configure(api_key=GEMINI_API_KEY)
    
    # --- 自动探测可用模型 (核心修复) ---
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        print(f"✅ 你的 Key 支持的模型有: {available_models}")
        # 自动选一个 1.5-flash 或者列表里第一个
        target = next((m for m in available_models if 'gemini-1.5-flash' in m), available_models[0])
    except Exception as e:
        print(f"⚠️ 无法探测模型，使用默认名: {e}")
        target = 'models/gemini-1.5-flash'

    print(f"🤖 选定模型: {target}")
    model = genai.GenerativeModel(target)

    # --- 2. 检索 PubMed ---
    print("📡 正在检索 PubMed...")
    query = '("Pulmonary Fibrosis"[Title/Abstract] OR "Bronchoscopy"[Title/Abstract]) AND ("last 30 days"[DP])'
    handle = Entrez.esearch(db="pubmed", term=query, retmax=10, sort="relevance")
    record = Entrez.read(handle)
    handle.close()
    
    id_list = record.get("IdList", [])
    paper_list = []

    if id_list:
        print(f"🔎 找到 {len(id_list)} 篇文献")
        fetch_handle = Entrez.efetch(db="pubmed", id=id_list, rettype="medline", retmode="text")
        records = list(Medline.parse(fetch_handle))
        fetch_handle.close()

        for r in records:
            title = r.get("TI", "No Title")
            abstract = r.get("AB", "")
            print(f"📝 正在处理: {title[:40]}...")
            
            # AI 总结逻辑
            summary = "无摘要内容。"
            if abstract:
                try:
                    res = model.generate_content(f"请用中文总结这篇医学文献的核心结论(40字内): {abstract[:1000]}")
                    summary = res.text.strip()
                except Exception as e:
                    summary = f"总结生成失败 ({str(e)[:20]})"
            
            paper_list.append({
                "title": title,
                "journal": r.get("TA", "Unknown"),
                "date": r.get("DP", "No Date"),
                "authors": ", ".join(r.get("AU", [])),
                "link": f"https://pubmed.ncbi.nlm.nih.gov/{r.get('PMID')}/",
                "summary": summary
            })
            time.sleep(1)

    # --- 3. 保存结果 ---
    os.makedirs('docs', exist_ok=True)
    with open('docs/data.json', 'w', encoding='utf-8') as f:
        json.dump(paper_list, f, ensure_ascii=False, indent=4)
    print("✅ 任务完成，数据已存入 docs/data.json")

if __name__ == "__main__":
    main()
