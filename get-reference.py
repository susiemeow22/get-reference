import os
import json
import time
from Bio import Entrez, Medline
import google.generativeai as genai

# 配置
Entrez.email = "test@test.com"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def main():
    print("🚀 开始运行...")
    if not GEMINI_API_KEY:
        print("❌ 未设置 API KEY")
        return

    # 初始化 AI
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # 检索 PubMed
    query = '("Pulmonary Fibrosis"[Title/Abstract] OR "Bronchoscopy"[Title/Abstract]) AND ("last 30 days"[DP])'
    handle = Entrez.esearch(db="pubmed", term=query, retmax=10)
    record = Entrez.read(handle)
    handle.close()
    
    id_list = record.get("IdList", [])
    paper_list = []

    if id_list:
        print(f"找到 {len(id_list)} 篇文献")
        fetch_handle = Entrez.efetch(db="pubmed", id=id_list, rettype="medline", retmode="text")
        records = list(Medline.parse(fetch_handle))
        fetch_handle.close()

        for r in records:
            title = r.get("TI", "No Title")
            abstract = r.get("AB", "")
            print(f"📄 处理: {title[:30]}...")
            
            # 简化 AI 总结
            summary = "暂无 AI 总结"
            if abstract:
                try:
                    res = model.generate_content(f"简述结论(40字内): {abstract[:1500]}")
                    summary = res.text.strip()
                except:
                    summary = "AI 总结生成失败"
            
            paper_list.append({
                "title": title,
                "journal": r.get("TA", "Unknown"),
                "date": r.get("DP", "No Date"),
                "authors": ", ".join(r.get("AU", [])),
                "link": f"https://pubmed.ncbi.nlm.nih.gov/{r.get('PMID')}/",
                "summary": summary
            })
            time.sleep(1)

    # 保存
    os.makedirs('docs', exist_ok=True)
    with open('docs/data.json', 'w', encoding='utf-8') as f:
        json.dump(paper_list, f, ensure_ascii=False, indent=4)
    print("✅ 完成")

if __name__ == "__main__":
    main()
