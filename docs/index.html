<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>呼吸文献速递</title>
    
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    
    <style>
        body { background-color: #f0f2f5; }
        .container { max-width: 600px; margin: 0 auto; }
        .card {
            background: white;
            border-radius: 16px;
            margin: 12px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }
        /* 标题限制在 3 行 */
        .title-clamp {
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
            font-size: 1.1rem;
            line-height: 1.4;
        }
    </style>
</head>
<body>
    <div id="app" class="container">
        <!-- 顶部导航 -->
        <header class="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-gray-100 py-4 px-6">
            <h1 class="text-xl font-extrabold text-gray-900 tracking-tight">🫁 呼吸文献精选</h1>
            <p class="text-[10px] text-gray-400 uppercase mt-1">Pulmonary Fibrosis & Bronchoscopy</p>
        </header>

        <!-- 加载提示 -->
        <div v-if="loading" class="text-center py-20 text-gray-400">
            <div class="animate-bounce text-3xl mb-2">🔄</div>
            <p>正在同步云端文献...</p>
        </div>

        <!-- 列表 -->
        <main v-else>
            <div v-for="(paper, index) in papers" :key="index" class="card" @click="openUrl(paper.link)">
                <!-- 杂志和日期 -->
                <div class="flex justify-between items-center mb-3">
                    <span class="bg-blue-100 text-blue-700 text-[10px] px-2 py-1 rounded font-bold uppercase">
                        {{ paper.journal }}
                    </span>
                    <span class="text-xs text-gray-400">{{ paper.date.split(' ')[0] }}</span>
                </div>

                <!-- 标题 -->
                <h2 class="title-clamp font-bold text-gray-900 mb-4">
                    {{ paper.title }}
                </h2>

                <!-- AI 总结：单列布局下可以放更多文字 -->
                <div class="bg-orange-50 border-l-4 border-orange-400 p-4 mb-4">
                    <p class="text-[14px] text-orange-900 leading-relaxed italic">
                        “ {{ paper.summary }} ”
                    </p>
                </div>

                <!-- 作者和链接按钮 -->
                <div class="flex justify-between items-end">
                    <div class="text-[11px] text-gray-500 italic w-2/3">
                        {{ paper.authors.split(',').slice(0, 2).join(', ') }} 等
                    </div>
                    <button class="text-xs font-bold text-blue-600 border border-blue-600 px-3 py-1 rounded-full active:bg-blue-50">
                        查看原文
                    </button>
                </div>
            </div>
        </main>
        
        <footer class="py-10 text-center text-gray-300 text-xs">
            已加载全部内容
        </footer>
    </div>

    <script>
        const { createApp, ref, onMounted } = Vue;
        createApp({
            setup() {
                const papers = ref([]);
                const loading = ref(true);

                const loadData = async () => {
                    try {
                        const response = await fetch('./data.json?t=' + new Date().getTime());
                        papers.value = await response.json();
                    } catch (err) {
                        console.error(err);
                    } finally {
                        loading.value = false;
                    }
                };

                const openUrl = (url) => window.open(url, '_blank');
                onMounted(loadData);
                return { papers, loading, openUrl };
            }
        }).mount('#app');
    </script>
</body>
</html>
