#!/usr/bin/env python3
"""
静态站点生成器
将Flask应用转换为静态HTML页面，用于GitHub Pages部署
"""

import os
import json
import shutil
from pathlib import Path
from flask import Flask
from app import app
import requests
from urllib.parse import urljoin


class StaticSiteGenerator:
    def __init__(self, output_dir="dist", base_url="/werewolf/"):
        self.app = app
        self.output_dir = Path(output_dir)
        self.base_url = base_url

    def generate(self):
        """生成静态站点"""
        print("Generating static site...")

        # 创建输出目录
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        with self.app.test_client() as client:
            # 生成主页
            self._generate_page(client, "/", "index.html")

            # 生成学习链页面
            self._generate_learning_chain_pages(client)

            # 复制静态文件
            self._copy_static_files()

            # 生成游戏列表API
            self._generate_api_files(client)

            # 生成每个游戏的页面
            self._generate_game_pages(client)

        print(f"Static site generated in {self.output_dir}")

    def _generate_page(self, client, url, filename):
        """生成单个页面"""
        response = client.get(url)
        if response.status_code == 200:
            content = response.get_data(as_text=True)
            # 修复静态资源路径，添加baseUrl前缀
            content = self._fix_static_urls(content)
            page_file = self.output_dir / filename
            page_file.write_text(content, encoding="utf-8")
            print(f"Generated: {filename}")
        else:
            print(f"Failed to generate {url}: {response.status_code}")

    def _fix_static_urls(self, content):
        """修复HTML中的静态资源URL，添加baseUrl前缀"""
        import re

        # 修复静态文件路径 href="/static/" -> href="/werewolf/static/"
        content = re.sub(r'href="/static/', f'href="{self.base_url}static/', content)

        # 修复静态文件路径 src="/static/" -> src="/werewolf/static/"
        content = re.sub(r'src="/static/', f'src="{self.base_url}static/', content)

        # 修复静态文件路径 href="static/" -> href="/werewolf/static/"
        content = re.sub(r'href="static/', f'href="{self.base_url}static/', content)

        # 修复API路径 href="/api/" -> href="/werewolf/api/"
        content = re.sub(r'href="/api/', f'href="{self.base_url}api/', content)

        # 修复CSS中的API路径 url("/api/") -> url("/werewolf/api/")
        content = re.sub(r'url\("/api/', f'url("{self.base_url}api/', content)
        content = re.sub(r"url\('/api/", f"url('{self.base_url}api/", content)

        # 修复相对链接路径 href="learning-chain/ -> href="/werewolf/learning-chain/
        content = re.sub(
            r'href="learning-chain/', f'href="{self.base_url}learning-chain/', content
        )
        content = re.sub(r'href="games/', f'href="{self.base_url}games/', content)

        return content

    def _copy_static_files(self):
        """复制静态文件"""
        static_source = Path("static")
        static_target = self.output_dir / "static"

        if static_source.exists():
            shutil.copytree(static_source, static_target, dirs_exist_ok=True)
            print("Copied static files")

        # 修复JavaScript中的URL路径
        self._fix_javascript_urls()

        # 修复静态HTML文件中的URL路径
        self._fix_static_html_files()

        # 复制.training目录到static目录中
        training_source = Path("..") / ".training"
        training_target = static_target / ".training"

        if training_source.exists():
            shutil.copytree(training_source, training_target, dirs_exist_ok=True)
            print("Copied .training directory to static")
        else:
            print("Warning: .training directory not found")

    def _fix_javascript_urls(self):
        """修复JavaScript文件中的URL路径"""
        js_file = self.output_dir / "static" / "script.js"
        if js_file.exists():
            content = js_file.read_text(encoding="utf-8")

            # 修复API路径，添加baseUrl前缀
            import re

            content = re.sub(r"'/api/", f"'{self.base_url}api/", content)
            content = re.sub(r'"/api/', f'"{self.base_url}api/', content)
            content = re.sub(r"`/api/", f"`{self.base_url}api/", content)

            # 修复特定API调用以使用静态文件
            # 修复 /werewolf/api/load/${filename} 调用，添加 .json 后缀
            content = re.sub(
                r"fetch\(`([^`]*)/api/load/\$\{([^}]+)\}`\)",
                r"fetch(`\1/api/load/${\2}.json`)",
                content,
            )

            # 添加静态部署标识和错误处理
            static_deployment_code = """
// Static deployment configuration
window.STATIC_DEPLOYMENT = true;

// Override fetch for static deployment error handling
const originalFetch = window.fetch;
window.fetch = async function(...args) {
    try {
        const response = await originalFetch(...args);
        if (!response.ok && window.STATIC_DEPLOYMENT) {
            // For static deployment, some APIs are not available
            const url = args[0];
            if (url.includes('/api/state') || url.includes('/api/reset') || 
                url.includes('/api/prev') || url.includes('/api/next') || 
                url.includes('/api/jump') || url.includes('/api/overview')) {
                console.warn('API not available in static deployment:', url);
                return new Response(JSON.stringify({error: 'API not available in static deployment'}), {
                    status: 200,
                    headers: {'Content-Type': 'application/json'}
                });
            }
        }
        return response;
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
};

"""

            content = static_deployment_code + content

            js_file.write_text(content, encoding="utf-8")
            print("Fixed JavaScript URLs and added static deployment support")

    def _fix_static_html_files(self):
        """修复静态HTML文件中的URL路径"""
        import re

        # 处理doc.html等静态HTML文件
        for html_file in (self.output_dir / "static").glob("*.html"):
            content = html_file.read_text(encoding="utf-8")

            # 修复 /api/ 路径
            content = re.sub(r'"/api/', f'"{self.base_url}api/', content)
            content = re.sub(r"'/api/", f"'{self.base_url}api/", content)
            content = re.sub(r"\(/api/", f"({self.base_url}api/", content)

            # 修复 url(&quot;/api/xxx&quot;) 这样的HTML编码的路径
            content = re.sub(
                r"url\(&quot;/api/", f"url(&quot;{self.base_url}api/", content
            )

            # 为doc.html添加返回首页按钮
            if html_file.name == "doc.html":
                home_button_html = """
<div style="position: fixed; top: 20px; left: 20px; z-index: 9999;">
    <a href="../index.html" style="
        background: rgba(102, 126, 234, 0.9);
        color: white;
        text-decoration: none;
        padding: 12px 20px;
        border-radius: 25px;
        font-weight: bold;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    " onmouseover="this.style.background='rgba(102, 126, 234, 1)'; this.style.transform='translateY(-2px)'" 
       onmouseout="this.style.background='rgba(102, 126, 234, 0.9)'; this.style.transform='translateY(0)'">
        🏠 返回首页
    </a>
</div>"""
                # 在body标签开始后插入按钮
                content = re.sub(r"(<body[^>]*>)", r"\1" + home_button_html, content)

            html_file.write_text(content, encoding="utf-8")
            print(f"Fixed URLs in {html_file.name}")
            if html_file.name == "doc.html":
                print("Added home button to doc.html")

    def _generate_api_files(self, client):
        """生成API文件"""
        api_dir = self.output_dir / "api"
        api_dir.mkdir(exist_ok=True)

        # 游戏列表API
        response = client.get("/api/games")
        if response.status_code == 200:
            games_file = api_dir / "games.json"
            games_file.write_text(response.get_data(as_text=True), encoding="utf-8")
            print("Generated: api/games.json")

        # 生成日志列表API
        logs_response = client.get("/api/logs")
        if logs_response.status_code == 200:
            logs_file = api_dir / "logs.json"
            logs_file.write_text(logs_response.get_data(as_text=True), encoding="utf-8")
            print("Generated: api/logs.json")

        # 为每个日志文件生成加载API
        if logs_response.status_code == 200:
            logs_data = logs_response.get_json()
            load_dir = api_dir / "load"
            load_dir.mkdir(exist_ok=True)

            for log in logs_data:
                filename = log["filename"]
                load_response = client.get(f"/api/load/{filename}")
                if load_response.status_code == 200:
                    load_file = load_dir / f"{filename}.json"
                    load_file.write_text(
                        load_response.get_data(as_text=True), encoding="utf-8"
                    )
                    print(f"Generated: api/load/{filename}.json")

    def _generate_learning_chain_pages(self, client):
        """生成学习链页面"""
        roles = ["seer", "werewolf", "witch", "villager", "guardian", "hunter"]
        learning_chain_dir = self.output_dir / "learning-chain"
        learning_chain_dir.mkdir(exist_ok=True)

        for role in roles:
            response = client.get(f"/learning-chain/{role}")
            if response.status_code == 200:
                content = response.get_data(as_text=True)
                # 修复静态资源路径
                content = self._fix_static_urls(content)
                role_file = learning_chain_dir / f"{role}.html"
                role_file.write_text(content, encoding="utf-8")
                print(f"Generated: learning-chain/{role}.html")

    def _generate_game_pages(self, client):
        """为每个游戏生成详细页面"""
        # 获取游戏列表
        response = client.get("/api/games")
        if response.status_code != 200:
            return

        games = response.get_json()
        games_dir = self.output_dir / "games"
        games_dir.mkdir(exist_ok=True)

        for game in games:
            game_id = game["id"]

            # 生成游戏数据API
            game_response = client.get(f"/api/game/{game_id}")
            if game_response.status_code == 200:
                game_file = games_dir / f"{game_id}.json"
                game_file.write_text(
                    game_response.get_data(as_text=True), encoding="utf-8"
                )
                print(f"Generated: games/{game_id}.json")


def create_github_pages_config():
    """创建GitHub Pages配置"""
    config = {
        "name": "狼人杀游戏回放可视化",
        "description": "基于Flask的狼人杀游戏日志可视化和回放系统",
        "url": "https://zhangzrjerry.github.io/werewolf",
        "baseurl": "/werewolf",
    }

    with open("dist/_config.yml", "w", encoding="utf-8") as f:
        for key, value in config.items():
            f.write(f"{key}: {value}\n")

    print("Created GitHub Pages config")


def create_spa_fallback():
    """创建SPA路由fallback"""
    # 为了支持单页应用路由，创建404.html指向index.html
    fallback_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Redirecting...</title>
    <script>
        // GitHub Pages SPA fallback for /werewolf/
        const pathSegments = location.pathname.split('/').filter(s => s);
        const expectedBase = 'werewolf';
        
        if (pathSegments[0] !== expectedBase) {
            // Redirect to the correct base path
            sessionStorage.redirect = location.href;
            location.replace(location.origin + '/werewolf/');
        } else {
            // Redirect to index.html with the original path stored
            sessionStorage.redirect = location.href;
            location.replace(location.origin + '/werewolf/');
        }
    </script>
</head>
<body>
    Redirecting to werewolf game visualization...
</body>
</html>"""

    with open("dist/404.html", "w", encoding="utf-8") as f:
        f.write(fallback_content)

    print("Created SPA fallback")


def main():
    # 检查是否在visualization目录中
    if not Path("app.py").exists():
        print("Error: Must run from visualization directory")
        return

    generator = StaticSiteGenerator()
    generator.generate()

    # GitHub Pages特定配置
    create_github_pages_config()
    create_spa_fallback()

    print("\n=== Static Site Generation Complete ===")
    print("Ready for GitHub Pages deployment")


if __name__ == "__main__":
    main()
