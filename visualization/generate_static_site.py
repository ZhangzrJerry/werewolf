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
    def __init__(self, output_dir="dist"):
        self.app = app
        self.output_dir = Path(output_dir)
        self.base_url = "/"

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
            page_file = self.output_dir / filename
            page_file.write_text(response.get_data(as_text=True), encoding="utf-8")
            print(f"Generated: {filename}")
        else:
            print(f"Failed to generate {url}: {response.status_code}")

    def _copy_static_files(self):
        """复制静态文件"""
        static_source = Path("static")
        static_target = self.output_dir / "static"

        if static_source.exists():
            shutil.copytree(static_source, static_target, dirs_exist_ok=True)
            print("Copied static files")

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
        // GitHub Pages SPA fallback
        sessionStorage.redirect = location.href;
        location.replace(location.origin + location.pathname.split('/').slice(0, -1).join('/') + '/');
    </script>
</head>
<body>
    Redirecting...
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
