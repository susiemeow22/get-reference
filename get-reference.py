import os
import json
import time
from Bio import Entrez, Medline
import google.generativeai as genai

# --- 1. 配置信息 ---
Entrez.email = "你的邮箱@example.com" 
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ 错误: 未找到 GEMINI_API_KEY，请检查 GitHub Secrets 设置")
else:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

SEARCH_QUERY = '("Pulmonary Fibrosis"[Title/Abstract] OR "Bronchoscopy"[Title/Abstract]) AND ("last 30 days"[DP])'

def fetch_recent_papers():
    print("🚀 开始从 PubMed 检索文献...")
    handle = Entrez.esearch(db="pubmed", term=SEARCH_QUERY, retmax=10, sort="relevance")
    record = Entrez.read(handle)
    handle.close()
    id_list = record["IdList"]

    if not id_list:
        print("❌ 未找到相关文献。")
        return

    handle = Entrez.efetch(db="pubmed", id=id_list, rettype="medline", retmode="text")
    records = list(Medline.parse(handle))
    handle.close()

    paper_data_list = []
    
    # --- 逐篇处理 (改为单篇处理更稳定，避开批量解析错误) ---
    for record in records:
        title = record.get("TI", "No Title")
        abstract = record.get("AB", "No Abstract")
        journal = record.get("TA", "No Journal")
        pub_date = record.get("DP", "No Date")
        pmid = record.get("PMID", "")
        authors = ", ".join(record.get("AU", []))
        
        print(f"📄 正在处理: {title[:50]}...")
        
        summary = "无摘要，点击查看原文。"
        if abstract != "No Abstract":
            try:
                prompt = f"你是一个呼吸医学专家。请用中文一句话概括这篇文献的核心结论（40字以内）：\n标题: {title}\n摘要: {abstract}"
                response = model.generate_content(prompt)
                summary = response.text.strip()
                time.sleep(2) # 免费版加一点点延迟，防止被封
            except Exception as e:
                print(f"⚠️ AI 总结失败原因: {e}")
                summary = "AI 总结生成失败，请检查 API 状态。"

        paper_data_list.append({
            "title": title,
            "journal": journal,
            "date": pub_date,
            "authors": authors,
            "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "summary": summary
        })

    # --- 保存结果 ---
    os.makedirs('docs', exist_ok=True)
    with open('docs/data.json', 'w', encoding='utf-8') as f:
        json.dump(paper_data_list, f, ensure_ascii=False, indent=4)
    print(f"✅ 搞定！共处理 {len(paper_data_list)} 篇文献。")

if __name__ == "__main__":
    fetch_recent_papers()
