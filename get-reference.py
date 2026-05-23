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
        return "点击查看原文了解详情。"
    
    prompt = f"你是一个医学专家。请用中文一句话概括这篇文献的核心结论（40字以内）：\n标题: {title}\n摘要: {abstract}"
    
    try:
        # 使用更通用的生成配置
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
        # 如果报错，把报错信息精简返回，方便我们调试
        return f"AI总结暂时不可用 ({str(e)[:30]})"

def fetch_recent_papers():
    if not GEMINI_API_KEY:
        print("❌ 错误: 未找到 GEMINI_API_KEY")
        return

    genai.configure(api_key=GEMINI_API_KEY)
    
    # --- 动态选择模型，防止 404 ---
    try:
        # 尝试使用最标准的 1.5 Flash 名称
        model = genai.GenerativeModel('gemini-1.5-flash')
        # 测试一下是否可用，不可用会跳到 except
        print("💡 尝试启动模型: gemini-1.5-flash")
    except:
        print("⚠️ 默认模型启动失败，尝试备用模型名称...")
        model = genai.GenerativeModel('gemini-pro')

    print("🚀 开始从 PubMed 检索文献...")
    SEARCH_QUERY = '("Pulmonary Fibrosis"[Title/Abstract] OR "Bronchoscopy"[Title/Abstract]) AND ("last 30 days"[DP])'
    
    try:
        handle = Entrez.esearch(db="pubmed", term=SEARCH_QUERY, retmax=10, sort="relevance")
        record = Entrez.read(handle)
        handle.close()
        id_list = record["IdList"]
    except Exception as e:
        print(f"PubMed 搜索失败: {e}")
        return

    if not id_list:
        print("❌ 未找到文献")
        return

    handle = Entrez.efetch(db="pubmed", id=id_list, rettype="medline", retmode="text")
    records = list(Medline.parse(handle))
    handle.close()

    paper_data_list = []
    for record in records:
        title = record.get("TI", "No Title")
        abstract = record.get("AB", "No Abstract")
        journal = record.get("TA", "No Journal")
        pmid = record.get("PMID", "")
        
        print(f"📄 正在处理: {title[:50]}...")
        
        summary = get_ai_summary(model, title, abstract)
        time.sleep(1) # 稍作停顿

        paper_data_list.append({
            "title": title,
            "journal": journal,
            "date": record.get("DP", "No Date"),
            "authors": ", ".join(record.get("AU", [])),
            "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}//",
            "summary": summary
        })

    os.makedirs('docs', exist_ok=True)
    with open('docs/data.json', 'w', encoding='utf-8') as f:
        json.dump(paper_data_list, f, ensure_ascii=False, indent=4)
    print("✅ 全部完成！")

if __name__ == "__main__":
    fetch_recent_papers()
