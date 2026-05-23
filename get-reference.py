import os
import json
from Bio import Entrez, Medline
import google.generativeai as genai

# --- 1. 配置信息 ---
Entrez.email = "susiemeow22@outlook.com" 
GEMINI_API_KEY = "AIzaSyDY7CQwqjvByzqV5jbMykHF-MN7S8-ZH-4"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

SEARCH_QUERY = '("Pulmonary Fibrosis"[Title/Abstract] OR "Bronchoscopy"[Title/Abstract]) AND ("last 30 days"[DP])'

def fetch_recent_papers():
    print("🚀 开始从 PubMed 检索文献...")
    handle = Entrez.esearch(db="pubmed", term=SEARCH_QUERY, retmax=15, sort="relevance")
    record = Entrez.read(handle)
    handle.close()
    id_list = record["IdList"]

    if not id_list:
        print("❌ 未找到相关文献。")
        return

    handle = Entrez.efetch(db="pubmed", id=id_list, rettype="medline", retmode="text")
    records = list(Medline.parse(handle))
    handle.close()

    # --- 批量准备数据 ---
    batch_prompt_content = ""
    paper_data_list = []

    for i, record in enumerate(records):
        title = record.get("TI", "No Title")
        abstract = record.get("AB", "No Abstract")
        journal = record.get("TA", "No Journal")
        pub_date = record.get("DP", "No Date")
        pmid = record.get("PMID", "")
        authors = ", ".join(record.get("AU", []))
        
        paper_data_list.append({
            "title": title,
            "journal": journal,
            "date": pub_date,
            "authors": authors,
            "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        })
        # 拼接给 AI 的内容
        batch_prompt_content += f"文献 {i+1}:\n标题: {title}\n摘要: {abstract}\n\n"

    # --- 一次性调用 Gemini ---
    print(f"🤖 正在请 Gemini 批量总结 {len(paper_data_list)} 篇文献...")
    full_prompt = f"""
    你是一个呼吸医学专家。请为以下多篇文献分别写一句话中文核心结论。
    要求：
    1. 每篇文献的总结不超过40个字。
    2. 按顺序排列，格式为：“1. [总结内容]”、“2. [总结内容]”。
    3. 直接给结论，不要解释。

    {batch_prompt_content}
    """

    try:
        response = model.generate_content(full_prompt)
        summaries = response.text.strip().split('\n')
        # 简单的结果匹配
        for i, paper in enumerate(paper_data_list):
            # 找到对应序号的内容
            summary_line = [s for s in summaries if s.startswith(f"{i+1}.")]
            if summary_line:
                paper["summary"] = summary_line[0].replace(f"{i+1}. ", "").strip()
            else:
                paper["summary"] = "点击查看详情。"
    except Exception as e:
        print(f"AI 批量总结出错: {e}")
        for paper in paper_data_list: paper["summary"] = "总结生成失败。"

    # --- 保存结果 ---
    if not os.path.exists('docs'): os.makedirs('docs')
    with open('docs/data.json', 'w', encoding='utf-8') as f:
        json.dump(paper_data_list, f, ensure_ascii=False, indent=4)
    
    print(f"✅ 搞定！数据已更新至 docs/data.json")

if __name__ == "__main__":
    fetch_recent_papers()