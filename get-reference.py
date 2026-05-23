import os
import json
import time
from Bio import Entrez, Medline
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# --- 配置 ---
Entrez.email = "你的邮箱@example.com"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def get_ai_summary(model, title, abstract):
    if not abstract or abstract == "No Abstract":
        return "摘要缺失，请点击查看原文。"
    
    prompt = f"你是一个医学专家。请用中文一句话概括这篇文献的核心结论（40字以内）：\n标题: {title}\n摘要: {abstract}"
    
    try:
        response = model.generate_content(
            prompt,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        return response.text.strip()
    except Exception as e:
        return f"总结失败: {str(e)[:30]}"

def fetch_recent_papers():
    if not GEMINI_API_KEY:
        print("❌ 未找到 GEMINI_API_KEY")
        return

    genai.configure(api_key=GEMINI_API_KEY)
    
    # --- 自动探测可用模型 (解决 404 核心逻辑) ---
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    print(f"💡 你的 Key 支持的模型有: {available_models}")
    
    target_model = None
    # 优先顺序：1.5-flash -> 1.5-pro -> 1.0-pro
    for preferred in ['models/gemini-1.5-flash', 'models/gemini-1.5-flash-latest', 'models/gemini-pro']:
        if preferred in available_models:
            target_model = preferred
            break
    
    if not target_model:
        target_model = available_models[0] if available_models else None

    if not target_model:
        print("❌ 没找到任何可用模型")
        return

    print(f"✅ 最终选择模型: {target_model}")
    model = genai.GenerativeModel(target_model)

    print("🚀 开始检索 PubMed...")
    SEARCH_QUERY = '("Pulmonary Fibrosis"[Title/Abstract] OR "Bronchoscopy"[Title/Abstract]) AND ("last 30 days"[DP])'
    handle = Entrez.esearch(db="pubmed", term=SEARCH_QUERY, retmax=10, sort="relevance")
    record = Entrez.read(handle)
    handle.close()
    
    id_list = record["IdList"]
    if not id_list: return

    handle = Entrez.efetch(db="pubmed", id=id_list, rettype="medline", retmode="text")
    records = list(Medline.parse(handle))
    handle.close()

    paper_data_list = []
    for record in records:
        title = record.get("TI", "No Title")
        abstract = record.get("AB", "No Abstract")
        journal = record.get("TA", "No Journal")
        pmid = record.get("PMID", "")
        
        print(f"📄 正在处理: {title[:40]}...")
        summary = get_ai_summary(model, title, abstract)
        time.sleep(1)

        paper_data_list.append({
            "title": title,
            "journal": journal,
            "date": record.get("DP", "No Date"),
            "authors": ", ".join(record.get("AU", [])),
            "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "summary": summary
        })

    os.makedirs('docs', exist_ok=True)
    with open('docs/data.json', 'w', encoding='utf-8') as f:
        json.dump(paper_data_list, f, ensure_ascii=False, indent=4)
    print("✅ 处理完成！")

if __name__ == "__main__":
    fetch_recent_papers()
