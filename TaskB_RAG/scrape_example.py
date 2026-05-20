#!/usr/bin/env python3
"""
数据采集示例脚本 — 从网络获取农业知识
- requests + BeautifulSoup 基础爬虫
- 处理中文网页编码
- 提取正文内容

⚠️ 重要说明：
这是一个示例脚本，使用通用的 HTML 解析策略。
不同的网站结构千差万别，此脚本不一定能直接适配你要爬取的网站。
你需要根据目标网站的实际 HTML 结构修改 extract_article() 中的查找逻辑。
有些网站使用了 JavaScript 动态加载内容，requests 无法获取。
有些网站有反爬机制，需要额外处理。
搜索 "Python 网页爬虫 BeautifulSoup 教程" 以学习更多技巧。
"""

import requests
from bs4 import BeautifulSoup
import time
import os


def fetch_page(url, encoding="utf-8"):
    """获取网页内容"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        # 有些中文网页用 GBK 编码
        if encoding == "auto":
            response.encoding = response.apparent_encoding
        else:
            response.encoding = encoding
        return response.text
    except Exception as e:
        print(f"请求失败: {e}")
        return None


def extract_article(html):
    """从网页中提取正文（简化版）"""
    soup = BeautifulSoup(html, "html.parser")

    # 删除脚本、样式、导航等无关元素
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # 尝试获取正文区域
    article = soup.find("article") or soup.find("div", class_="content") or soup.find("main")

    if article:
        text = article.get_text(separator="\n", strip=True)
    else:
        # 退而求其次，获取所有段落
        paragraphs = soup.find_all("p")
        text = "\n".join(
            [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50]
        )

    # 清理多余空行
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n\n".join(lines)


# ── 示例用法 ──
if __name__ == "__main__":
    # 示例 URL（需要替换为实际可抓取的农业知识网页）
    urls = [
        # "https://example-agri-site.com/tomato-disease-guide",
        # "https://example-agri-site.com/planting-guide",
    ]

    if not urls:
        print("请在代码中添加实际的农业知识网页 URL")
        print("推荐来源：中国农业信息网、各省市农业厅公开资料等")
        print("\n示例流程：")
        print("1. 找到一篇关于番茄病害的科普文章")
        print("2. 使用 fetch_page() 获取网页 HTML")
        print("3. 使用 extract_article() 提取正文")
        print("4. 保存到 knowledge_base/ 目录下")
        print("\n法律提示：")
        print("- 只采集公开数据，尊重 robots.txt")
        print("- 不要高频请求，每次间隔 2-3 秒")
        print("- 采集内容用于学习和研究，不要商用")
    else:
        os.makedirs("knowledge_base", exist_ok=True)
        for i, url in enumerate(urls):
            print(f"正在抓取第 {i + 1} 篇文章...")
            html = fetch_page(url, encoding="auto")
            if html:
                text = extract_article(html)
                filename = f"knowledge_base/article_{i + 1}.md"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"# 第{i + 1}篇文章\n\n")
                    f.write(f"来源: {url}\n\n")
                    f.write(text)
                print(f"已保存到 {filename}")
            time.sleep(2)  # 礼貌延迟
