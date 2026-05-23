import os
import json
import time
from Bio import Entrez, Medline
import google.generativeai as genai

# --- 基础配置 ---
Entrez.email = "your_med_app@test.com"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def main():
    print("🚀 程序启动...")
    if not GEMINI_API_KEY:
        print("❌ 未发现 API KEY，请检查 GitHub Secrets")
        return

    # 1. 初始化并寻找可用模型
    genai.configure(api_key=GEMINI_API_KEY)
    
    available_models = []
    try:
        # 获取该 Key 支持的所有模型
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        print(f"✅ 你的 Key 支持的模型: {available_models}")
    except Exception as e:
        print(f"⚠️ 无法获取模型列表: {e}")

    # 优先选 1.5-flash, 其次 1.5-pro, 最后选列表里第一个
    target_model = ""
    for candidate in ['models/gemini-1.5-flash', 'models/gemini-1.5-flash-latest', 'models/gemini-pro']:
        if candidate in available_models:
            target_model = candidate
            break
    
    if not target_model and available_models:
        target_model = available_models[0]
    
    if not target_model:
        # 如果连列表都取不到，强制试一下最新正式名
        target_model = "gemini-1.5-flash"
    
    print(f"🤖 选定模型: {target_model}")
    model = genai.GenerativeModel(target_model)

    # 2. 检索 PubMed
    print("📡 正在检索 PubMed 文献...")
    # 搜索关键词：肺纤维化 或 支气管镜
    query = '("Pulmonary Fibrosis"[Title/Abstract] OR "Bronchoscopy"[Title/Abstract]) AND ("last 30 days"[DP])'
    
    try:
        handle = Entrez.esearch(db="pubmed", term=query, retmax=10)
        record = Entrez.read(handle)
        handle.close()
        id_list = record.get("IdList", [])
    except Exception as e:
        print(f"PubMed 搜索失败: {e}")
        return

    paper_list = []
    if id_list:
        print(f"🔎 找到 {len(id_list)} 篇文献，开始总结...")
        fetch_handle = Entrez.efetch(db="pubmed", id=id_list, rettype="medline", retmode="text")
        records = list(Medline.parse(fetch_handle))
        fetch_handle.close()

        for r in records:
            title = r.get("TI", "No Title")
            abstract = r.get("AB", "")
            print(f"📝 正在处理: {title[:40]}...")
            
            # AI 总结
            summary = "无摘要可供总结。"
            if abstract:
                try:
                    # 简化 Prompt 提高成功率
                    prompt = f"请用中文一句话概括文献结论(40字内):\n标题:{title}\n摘要:{abstract[:1000]}"
                    response = model.generate_content(prompt)
                    summary = response.text.strip()
                except Exception as e:
                    summary = f"AI总结暂时不可用 (报错:{str(e)[:20]})"
            
            paper_list.append({
                "title": title,
                "journal": r.get("TA", "Unknown"),
                "date": r.get("DP", "No Date"),
                "authors": ", ".join(r.get("AU", [])),
                "link": f"https://pubmed.ncbi.nlm.nih.gov/{r.get('PMID')}/",
                "summary": summary
            })
            time.sleep(1) # 限速

    # 3. 保存
    os.makedirs('docs', exist_ok=True)
    with open('docs/data.json', 'w', encoding='utf-8') as f:
        json.dump(paper_list, f, ensure_ascii=False, indent=4)
    print(f"✅ 任务完成，保存了 {len(paper_list)} 篇文献")

if __name__ == "__main__":
    main()
