import os
import json
import time
from Bio import Entrez, Medline
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# --- 配置 ---
Entrez.email = "medical_app@test.com"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def get_summary(model, title, abstract):
    if not abstract: return "无摘要供总结。"
    # 这里的 Prompt 尽量简单，避开敏感词
    prompt = f"请简要总结下文核心结论(40字内):\n标题:{title}\n摘要:{abstract[:1000]}"
    try:
        # 关闭安全过滤，防止医学词汇被拦截
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
        # --- 这里的打印非常关键，请在 Action 日志里看它 ---
        print(f"❌ AI 报错详情: {str(e)}")
        return f"AI总结暂时不可用: {str(e)[:30]}"

def main():
    print("🚀 程序开始...")
    if not GEMINI_API_KEY:
        print("❌ 未设置 GEMINI_API_KEY Secret!")
        return

    # 初始化 AI
    genai.configure(api_key=GEMINI_API_KEY)
    
    # 尝试不同的模型名称 (解决 404 问题的终极方案)
    target_model_name = 'gemini-1.5-flash'
    try:
        model = genai.GenerativeModel(target_model_name)
        # 测试一下模型是否真正可用
        model.generate_content("Hi", request_options={'timeout': 10})
        print(f"✅ 模型 {target_model_name} 连接成功")
    except Exception as e:
        print(f"⚠️ 默认模型不可用，尝试备用模型: {e}")
        model = genai.GenerativeModel('gemini-pro')

    # 检索 PubMed
    query = '("Pulmonary Fibrosis"[Title/Abstract] OR "Bronchoscopy"[Title/Abstract]) AND ("last 30 days"[DP])'
    handle = Entrez.esearch(db="pubmed", term=query, retmax=10)
    record = Entrez.read(handle)
    handle.close()
    
    id_list = record.get("IdList", [])
    paper_list = []

    if id_list:
        print(f"🔎 发现 {len(id_list)} 篇文献，开始处理...")
        fetch_handle = Entrez.efetch(db="pubmed", id=id_list, rettype="medline", retmode="text")
        records = list(Medline.parse(fetch_handle))
        fetch_handle.close()

        for r in records:
            title = r.get("TI", "No Title")
            print(f"📝 正在总结: {title[:40]}...")
            
            summary = get_summary(model, title, r.get("AB", ""))
            time.sleep(1) # 免费版 QPS 限制

            paper_list.append({
                "title": title,
                "journal": r.get("TA", "Unknown"),
                "date": r.get("DP", "No Date"),
                "authors": ", ".join(r.get("AU", [])),
                "link": f"https://pubmed.ncbi.nlm.nih.gov/{r.get('PMID')}/",
                "summary": summary
            })

    # 保存
    os.makedirs('docs', exist_ok=True)
    with open('docs/data.json', 'w', encoding='utf-8') as f:
        json.dump(paper_list, f, ensure_ascii=False, indent=4)
    print("✅ 任务完成！数据已存入 docs/data.json")

if __name__ == "__main__":
    main()
