import os
import json
import time
from Bio import Entrez, Medline
from openai import OpenAI

# --- 配置 ---
Entrez.email = "medical_app@test.com"
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

def get_summary(client, title, abstract):
    if not abstract: return "摘要缺失，请点击查看原文。"
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个呼吸医学专家，请用中文一句话概括文献的核心结论，不超过40字。直接说结论。"},
                {"role": "user", "content": f"标题: {title}\n摘要: {abstract[:1500]}"}
            ],
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ AI 总结失败: {e}")
        return "AI 总结暂时不可用。"

def main():
    print("🚀 程序启动 (DeepSeek 版)...")
    if not DEEPSEEK_API_KEY:
        print("❌ 未发现 DEEPSEEK_API_KEY")
        return

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

    # 检索 PubMed
    print("📡 正在检索 PubMed...")
    query = '("Pulmonary Fibrosis"[Title/Abstract] OR "Bronchoscopy"[Title/Abstract]) AND ("last 30 days"[DP])'
    handle = Entrez.esearch(db="pubmed", term=query, retmax=10, sort="relevance")
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
            print(f"📝 正在总结: {title[:40]}...")
            
            summary = get_summary(client, title, abstract)
            
            paper_list.append({
                "title": title,
                "journal": r.get("TA", "Unknown"),
                "date": r.get("DP", "No Date"),
                "authors": ", ".join(r.get("AU", [])),
                "link": f"https://pubmed.ncbi.nlm.nih.gov/{r.get('PMID')}/",
                "summary": summary
            })
            # DeepSeek 速度很快，不需要像 Gemini 那样等很久

    # 保存
    os.makedirs('docs', exist_ok=True)
    with open('docs/data.json', 'w', encoding='utf-8') as f:
        json.dump(paper_list, f, ensure_ascii=False, indent=4)
    print("✅ 任务完成！")

if __name__ == "__main__":
    main()
