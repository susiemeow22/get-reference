import os
import json
import time
from Bio import Entrez, Medline
import google.generativeai as genai

Entrez.email = "medical_app@test.com"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def main():
    print("🚀 启动程序...")
    if not GEMINI_API_KEY:
        print("❌ 未发现 API KEY")
        return

    genai.configure(api_key=GEMINI_API_KEY)
    
    # --- 1. 自动探测可用模型 (核心修复代码) ---
    target_model_name = ""
    try:
        print("🔍 正在拉取你的 Key 支持的所有模型列表...")
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        print(f"✅ 你的可用模型列表: {models}")
        
        # 按照优先级排序寻找
        candidates = ['models/gemini-1.5-flash', 'models/gemini-1.5-flash-latest', 'models/gemini-1.0-pro', 'models/gemini-pro']
        for c in candidates:
            if c in models:
                target_model_name = c
                break
        
        if not target_model_name and models:
            target_model_name = models[0] # 实在找不到，就用列表里的第一个
    except Exception as e:
        print(f"⚠️ 无法自动探测模型，尝试手动指定: {e}")
        target_model_name = 'models/gemini-1.5-flash' # 最后的保底

    print(f"🤖 最终选定模型: {target_model_name}")
    model = genai.GenerativeModel(target_model_name)

    # --- 2. 检索 PubMed ---
    query = '("Pulmonary Fibrosis"[Title/Abstract] OR "Bronchoscopy"[Title/Abstract]) AND ("last 30 days"[DP])'
    handle = Entrez.esearch(db="pubmed", term=query, retmax=10)
    record = Entrez.read(handle)
    handle.close()
    
    paper_list = []
    if record["IdList"]:
        fetch_handle = Entrez.efetch(db="pubmed", id=record["IdList"], rettype="medline", retmode="text")
        records = list(Medline.parse(fetch_handle))
        fetch_handle.close()

        for r in records:
            title = r.get("TI", "No Title")
            abstract = r.get("AB", "")
            summary = "无摘要内容。"
            
            if abstract:
                try:
                    # 简化 Prompt，防止特殊字符导致 404 误报
                    res = model.generate_content(f"请用中文总结结论(40字内): {abstract[:1000]}")
                    summary = res.text.strip()
                except Exception as e:
                    # 如果还是报错，把具体的报错抓出来
                    summary = f"总结失败: {str(e)[:30]}"
            
            paper_list.append({
                "title": title, "journal": r.get("TA", "Unknown"),
                "date": r.get("DP", "No Date"), "authors": ", ".join(r.get("AU", [])),
                "link": f"https://pubmed.ncbi.nlm.nih.gov/{r.get('PMID')}/",
                "summary": summary
            })
            time.sleep(1)

    # --- 3. 保存 ---
    os.makedirs('docs', exist_ok=True)
    with open('docs/data.json', 'w', encoding='utf-8') as f:
        json.dump(paper_list, f, ensure_ascii=False, indent=4)
    print("✅ 任务完成")

if __name__ == "__main__":
    main()
