import os
import json
import time
import sys
import traceback
from Bio import Entrez, Medline
import google.generativeai as genai

# --- 1. 基础配置 ---
Entrez.email = "medical_researcher@example.com"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def get_ai_summary(model, title, abstract):
    """尝试获取AI总结，失败时不崩溃"""
    if not abstract or abstract == "No Abstract":
        return "摘要缺失，请查阅原文。"
    if not model:
        return "AI模型未启动，暂无总结。"
        
    prompt = f"你是一个医学专家。请用中文一句话概括这篇文献的核心结论：\n标题: {title}\n摘要: {abstract}"
    try:
        response = model.generate_content(prompt, request_options={'timeout': 20})
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ 某篇文献AI总结失败: {str(e)[:50]}")
        return "AI总结生成中或暂时不可用。"

def main():
    print("🎬 程序启动...")
    paper_list = []
    
    try:
        # 1. 检查 Key
        if not GEMINI_API_KEY:
            print("❌ 错误: GEMINI_API_KEY 环境变量缺失！")
            sys.exit(1)

        # 2. 初始化 AI
        model = None
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            # 直接尝试最常用的模型名
            model = genai.GenerativeModel('gemini-1.5-flash')
            print("✅ AI 模型初始化完成")
        except Exception as e:
            print(f"⚠️ AI 初始化失败，将仅抓取文献: {e}")

        # 3. 检索 PubMed
        print("📡 正在连接 PubMed...")
        query = '("Pulmonary Fibrosis"[Title/Abstract] OR "Bronchoscopy"[Title/Abstract]) AND ("last 30 days"[DP])'
        
        handle = Entrez.esearch(db="pubmed", term=query, retmax=10, sort="relevance")
        record = Entrez.read(handle)
        handle.close()
        
        id_list = record.get("IdList", [])
        if not id_list:
            print("📭 最近30天未找到相关文献。")
        else:
            print(f"🔎 找到 {len(id_list)} 篇文献，开始处理...")
            fetch_handle = Entrez.efetch(db="pubmed", id=id_list, rettype="medline", retmode="text")
            records = list(Medline.parse(fetch_handle))
            fetch_handle.close()

            for r in records:
                title = r.get("TI", "No Title")
                pmid = r.get("PMID", "0")
                print(f"📝 处理中: {title[:40]}...")
                
                # 获取 AI 总结
                summary = get_ai_summary(model, title, r.get("AB", "No Abstract"))
                time.sleep(1) # 限速

                paper_list.append({
                    "title": title,
                    "journal": r.get("TA", "Unknown"),
                    "date": r.get("DP", "No Date"),
                    "authors": ", ".join(r.get("AU", [])),
                    "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    "summary": summary
                })

        # 4. 保存数据 (无论是否有文献或AI是否成功，都保存)
        os.makedirs('docs', exist_ok=True)
        with open('docs/data.json', 'w', encoding='utf-8') as f:
            json.dump(paper_list, f, ensure_ascii=False, indent=4)
        print(f"🎉 任务结束！保存了 {len(paper_list)} 篇文献。")

    except Exception as e:
        print("🔥 发生致命错误:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
