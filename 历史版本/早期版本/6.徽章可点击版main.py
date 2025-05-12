import requests
import tkinter as tk
from tkinter import ttk, messagebox
import pyperclip
import os
import json
import threading
from datetime import datetime

class GitHubRepoInfoGenerator:
    CONFIG_DIR = os.path.expanduser("~/.config/gh_repo_info")
    CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
    
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub 仓库信息生成器")
        self.root.geometry("720x480")
        self.token = None
        self.current_tab = None
        self.show_user = tk.IntVar(value=0)
        self.show_stars = tk.IntVar(value=0)
        self.show_version = tk.IntVar(value=0)
        self.show_release_date = tk.IntVar(value=0)
        self.show_size = tk.IntVar(value=0)
        self.show_language = tk.IntVar(value=0)
        self.show_license = tk.IntVar(value=0)
        self.show_downloads = tk.IntVar(value=0)
        self.show_issues = tk.IntVar(value=0)
        self.show_build_status = tk.IntVar(value=0)
        self.show_docker_pulls = tk.IntVar(value=0)
        self.include_header = tk.IntVar(value=1)
        self.load_config()
        self.create_widgets()

    def create_widgets(self):
        self.main_canvas = tk.Canvas(self.root)
        self.main_scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.main_canvas.yview)
        self.main_canvas.configure(yscrollcommand=self.main_scrollbar.set)
        self.main_scrollbar.pack(side="right", fill="y")
        self.main_canvas.pack(side="left", fill="both", expand=True)
        self.main_frame = ttk.Frame(self.main_canvas)
        self.main_canvas.create_window((0, 0), window=self.main_frame, anchor="nw")
        self.main_frame.bind("<Configure>", lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all")))
        
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill="both", expand=True)
        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="无序列表")
        self.notebook.add(self.tab2, text="表格格式")
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        self.create_tab1()
        self.create_tab2()
        self.create_bottom_area()
        self.root.bind("<MouseWheel>", self.on_mousewheel)

    def create_tab1(self):
        token_frame = ttk.LabelFrame(self.tab1, text="GitHub Personal Access Token（可选）")
        token_frame.pack(pady=10, padx=10, fill="x")
        self.token_entry = ttk.Entry(token_frame, width=50, show="*")
        self.token_entry.pack(pady=5, padx=5, side="left", expand=True, fill="x")
        if self.token:
            self.token_entry.insert(0, self.token)
        ttk.Button(token_frame, text="设置Token", command=self.set_token).pack(pady=5, padx=5, side="right")

        input_frame = ttk.LabelFrame(self.tab1, text="GitHub 仓库（每行一个 user/repo）")
        input_frame.pack(pady=10, padx=10, fill="both")
        self.repo_text_tab1 = tk.Text(input_frame, width=50, height=5, font=('Consolas', 10))
        self.repo_text_tab1.pack(pady=5, padx=5, side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(input_frame, command=self.repo_text_tab1.yview)
        scrollbar.pack(side="right", fill="y", padx=(0, 5))
        self.repo_text_tab1.config(yscrollcommand=scrollbar.set)

        control_frame = ttk.Frame(self.tab1)
        control_frame.pack(pady=5, fill="x")
        self.create_checkbuttons(control_frame)
        ttk.Button(control_frame, text="生成", command=lambda: self.threaded_generate('tab1')).pack(side="right", padx=5)

        output_frame = ttk.LabelFrame(self.tab1, text="生成结果 - Markdown 无序列表")
        output_frame.pack(pady=10, padx=10, fill="both", expand=True)
        button_frame = ttk.Frame(output_frame)
        button_frame.pack(pady=5, fill="x")
        ttk.Button(button_frame, text="复制", command=lambda: self.copy_to_clipboard('tab1')).pack(side="right", padx=5)
        self.output_text_tab1 = tk.Text(output_frame, height=12, wrap="word", font=('Consolas', 10))
        self.output_text_tab1.pack(pady=5, padx=5, fill="both", expand=True)
        output_scrollbar = ttk.Scrollbar(output_frame, command=self.output_text_tab1.yview)
        output_scrollbar.pack(side="right", fill="y", padx=(0, 5))
        self.output_text_tab1.config(yscrollcommand=output_scrollbar.set)

    def create_tab2(self):
        input_frame = ttk.LabelFrame(self.tab2, text="GitHub 仓库（每行一个 user/repo）")
        input_frame.pack(pady=10, padx=10, fill="both")
        self.repo_text_tab2 = tk.Text(input_frame, width=50, height=5, font=('Consolas', 10))
        self.repo_text_tab2.pack(pady=5, padx=5, side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(input_frame, command=self.repo_text_tab2.yview)
        scrollbar.pack(side="right", fill="y", padx=(0, 5))
        self.repo_text_tab2.config(yscrollcommand=scrollbar.set)

        control_frame = ttk.Frame(self.tab2)
        control_frame.pack(pady=5, fill="x")
        ttk.Checkbutton(control_frame, text="生成表头", variable=self.include_header).pack(side="left", padx=5)
        self.create_checkbuttons(control_frame)
        ttk.Button(control_frame, text="生成", command=lambda: self.threaded_generate('tab2')).pack(side="right", padx=5)

        output_frame = ttk.LabelFrame(self.tab2, text="生成结果 - Markdown 表格")
        output_frame.pack(pady=10, padx=10, fill="both", expand=True)
        button_frame = ttk.Frame(output_frame)
        button_frame.pack(pady=5, fill="x")
        ttk.Button(button_frame, text="复制", command=lambda: self.copy_to_clipboard('tab2')).pack(side="right", padx=5)
        self.output_text_tab2 = tk.Text(output_frame, height=12, wrap="word", font=('Consolas', 10))
        self.output_text_tab2.pack(pady=5, padx=5, fill="both", expand=True)
        output_scrollbar = ttk.Scrollbar(output_frame, command=self.output_text_tab2.yview)
        output_scrollbar.pack(side="right", fill="y", padx=(0, 5))
        self.output_text_tab2.config(yscrollcommand=output_scrollbar.set)

    def create_checkbuttons(self, frame):
        check_frame = ttk.Frame(frame)
        check_frame.pack(side="left", fill="y")
        checkbuttons = [
            ("显示user", self.show_user),
            ("star数", self.show_stars),
            ("最新版本", self.show_version),
            ("发布/归档日期", self.show_release_date),
            ("仓库大小", self.show_size),
            ("编程语言", self.show_language),
            ("开源协议", self.show_license),
            ("下载量", self.show_downloads),
            ("issues数", self.show_issues),
            ("构建状态", self.show_build_status),
            ("Docker Pulls", self.show_docker_pulls)
        ]
        left_frame = ttk.Frame(check_frame)
        left_frame.pack(side="left", padx=5)
        right_frame = ttk.Frame(check_frame)
        right_frame.pack(side="left", padx=5)
        for i, (text, var) in enumerate(checkbuttons):
            target_frame = left_frame if i < 5 else right_frame
            ttk.Checkbutton(target_frame, text=text, variable=var).pack(anchor="w", pady=2)

    def create_bottom_area(self):
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def on_tab_change(self, event):
        selected_tab = self.notebook.index(self.notebook.select())
        self.current_tab = 'tab1' if selected_tab == 0 else 'tab2'

    def threaded_generate(self, tab):
        self.clear_output(tab)
        self.set_ui_state(False)
        self.status_var.set("正在获取仓库信息...")
        threading.Thread(target=lambda: self.generate_info(tab), daemon=True).start()

    def generate_info(self, tab):
        errors = []
        try:
            inputs = getattr(self, f'repo_text_{tab}').get("1.0", tk.END).strip().splitlines()
            valid_repos = [r.strip() for r in inputs if r.strip() and "/" in r]
            if not valid_repos:
                self.show_errors(["未输入有效仓库地址"])
                return

            headers = {"Authorization": f"token {self.token}"} if self.token else {}
            output_lines = []
            
            with requests.Session() as session:
                for repo in valid_repos:
                    user, repo_name = repo.split("/", 1)
                    try:
                        repo_res = session.get(
                            f"https://api.github.com/repos/{user}/{repo_name}",
                            headers=headers
                        )
                        repo_res.raise_for_status()
                        repo_data = repo_res.json()
                    except requests.exceptions.HTTPError as e:
                        errors.append(self.handle_http_error(e, repo))
                        continue

                    is_archived = repo_data.get('archived', False)
                    if is_archived and self.show_release_date.get():
                        pushed_at = repo_data.get('pushed_at', '')
                        if pushed_at:
                            last_commit_date = datetime.strptime(
                                pushed_at, "%Y-%m-%dT%H:%M:%SZ"
                            ).strftime("%Y-%m-%d").replace('-', '--')
                            release_badge = f"![Archived](https://img.shields.io/badge/Archived-{last_commit_date}-red?style=flat)"
                        else:
                            release_badge = f"![Archived](https://img.shields.io/badge/Archived-unknown-red?style=flat)"
                    elif self.show_release_date.get():
                        release_badge = f"![Latest Release](https://img.shields.io/github/release-date/{user}/{repo_name}?label=Latest+Release&style=flat)"
                    else:
                        release_badge = ""

                    link_text = f"{user}/{repo_name}" if self.show_user.get() else repo_name
                    link = f"- [{link_text}](https://github.com/{user}/{repo_name})" if tab == 'tab1' else f"[{link_text}](https://github.com/{user}/{repo_name})"

                    badges = []
                    if self.show_stars.get():
                        badges.append(f"[![Stars](https://img.shields.io/github/stars/{user}/{repo_name}?style=flat)](https://github.com/{user}/{repo_name}/stargazers)")
                    if self.show_version.get():
                        badges.append(f"[![Version](https://img.shields.io/github/v/tag/{user}/{repo_name}?label=Version&style=flat)](https://github.com/{user}/{repo_name}/releases)")
                    if self.show_release_date.get():
                        if is_archived:
                            badges.append(release_badge)
                        else:
                            badges.append(f"[![Latest Release](https://img.shields.io/github/release-date/{user}/{repo_name}?label=Latest+Release&style=flat)](https://github.com/{user}/{repo_name}/releases)")
                    if self.show_size.get():
                        size_mb = repo_data.get('size', 0) / 1024
                        badges.append(f"![Size](https://img.shields.io/badge/Size-{size_mb:.2f}MB-blue?style=flat)")
                    if self.show_language.get():
                        badges.append(f"[![Language](https://img.shields.io/github/languages/top/{user}/{repo_name}?style=flat)](https://github.com/{user}/{repo_name}/search?l={repo_data.get('language', '')})")
                    if self.show_license.get():
                        badges.append(f"[![License](https://img.shields.io/github/license/{user}/{repo_name}?style=flat)](https://github.com/{user}/{repo_name}/blob/master/LICENSE)")
                    if self.show_downloads.get():
                        badges.append(f"[![Downloads](https://img.shields.io/github/downloads/{user}/{repo_name}/total?style=flat)](https://github.com/{user}/{repo_name}/releases)")
                    if self.show_issues.get():
                        badges.append(f"[![Issues](https://img.shields.io/github/issues/{user}/{repo_name}?style=flat)](https://github.com/{user}/{repo_name}/issues)")
                    if self.show_build_status.get():
                        badges.append(f"[![Build](https://img.shields.io/github/workflow/status/{user}/{repo_name}/build?style=flat)](https://github.com/{user}/{repo_name}/actions)")
                    if self.show_docker_pulls.get():
                        description = repo_data.get('description', '')
                        if 'docker.io' in description:
                            docker_repo = description.split('docker.io/')[1].split()[0]
                            badges.append(f"[![Docker Pulls](https://img.shields.io/docker/pulls/{docker_repo}?style=flat)](https://hub.docker.com/r/{docker_repo})")

                    if tab == 'tab1':
                        if badges:
                            output_lines.append(f"{link}\n  {'  '.join(badges)}\n")
                        else:
                            output_lines.append(f"{link}\n")
                    else:
                        formatted_badges = '<br>'.join(badges) if badges else ""
                        output_lines.append(f"| {link} | {formatted_badges} |  |")

            md_content = self.build_output(tab, output_lines)
            self.update_output(md_content, tab)
            self.status_var.set("生成成功")
            if errors:
                self.show_errors(errors)
                
        except Exception as e:
            self.show_error(f"生成过程中发生异常: {str(e)}")
        finally:
            self.set_ui_state(True)

    def build_output(self, tab, lines):
        if tab == 'tab1':
            return "\n".join(lines)
        header = "| 项目 | 徽章 | 说明 |\n|------|------|------|\n" if self.include_header.get() else ""
        return header + "\n".join(lines)

    def handle_http_error(self, error, repo):
        status_code = error.response.status_code
        if status_code == 403:
            return f"API请求次数超限：{repo}（请设置Token）"
        if status_code == 404:
            return f"仓库不存在：{repo}"
        if status_code == 401:
            return f"Token无效：{repo}"
        return f"HTTP错误 {status_code}：{repo}"

    def show_errors(self, errors):
        messagebox.showwarning("处理完成但存在错误", "\n".join(errors))
        self.status_var.set(f"生成完成，存在{len(errors)}个错误")

    def set_ui_state(self, enabled):
        state = "normal" if enabled else "disabled"
        for tab in ['tab1', 'tab2']:
            getattr(self, f'repo_text_{tab}').config(state=state)
        self.token_entry.config(state=state)
        self.root.config(cursor="" if enabled else "watch")
        self.root.update()

    def clear_output(self, tab):
        output_widget = getattr(self, f'output_text_{tab}')
        output_widget.config(state="normal")
        output_widget.delete(1.0, tk.END)
        output_widget.config(state="disabled")

    def update_output(self, content, tab):
        output_widget = getattr(self, f'output_text_{tab}')
        output_widget.config(state="normal")
        output_widget.delete(1.0, tk.END)
        output_widget.insert(tk.END, content)
        output_widget.config(state="disabled")

    def copy_to_clipboard(self, tab):
        output_widget = getattr(self, f'output_text_{tab}')
        text = output_widget.get(1.0, tk.END).strip()
        if text:
            pyperclip.copy(text)
            self.status_var.set("内容已复制到剪贴板")

    def show_error(self, message):
        messagebox.showerror("错误", message)
        self.status_var.set(message)

    def load_config(self):
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.token = config.get('token')
                    self.show_user.set(config.get('show_user', 0))
                    self.show_stars.set(config.get('show_stars', 0))
                    self.show_version.set(config.get('show_version', 0))
                    self.show_release_date.set(config.get('show_release_date', 0))
                    self.show_size.set(config.get('show_size', 0))
                    self.show_language.set(config.get('show_language', 0))
                    self.show_license.set(config.get('show_license', 0))
                    self.show_downloads.set(config.get('show_downloads', 0))
                    self.show_issues.set(config.get('show_issues', 0))
                    self.show_build_status.set(config.get('show_build_status', 0))
                    self.show_docker_pulls.set(config.get('show_docker_pulls', 0))
        except Exception as e:
            self.show_error(f"加载配置失败: {str(e)}")

    def save_config(self):
        try:
            os.makedirs(self.CONFIG_DIR, exist_ok=True)
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump({
                    'token': self.token,
                    'show_user': self.show_user.get(),
                    'show_stars': self.show_stars.get(),
                    'show_version': self.show_version.get(),
                    'show_release_date': self.show_release_date.get(),
                    'show_size': self.show_size.get(),
                    'show_language': self.show_language.get(),
                    'show_license': self.show_license.get(),
                    'show_downloads': self.show_downloads.get(),
                    'show_issues': self.show_issues.get(),
                    'show_build_status': self.show_build_status.get(),
                    'show_docker_pulls': self.show_docker_pulls.get()
                }, f)
            if os.name != 'nt':
                os.chmod(self.CONFIG_FILE, 0o600)
        except Exception as e:
            self.show_error(f"保存配置失败: {str(e)}")

    def set_token(self):
        new_token = self.token_entry.get().strip()
        if new_token != self.token:
            self.token = new_token or None
            self.save_config()
            self.status_var.set(f"Token {'已更新' if self.token else '已清除'}")
        else:
            self.status_var.set("Token未变化")

    def on_mousewheel(self, event):
        widget = event.widget
        if widget in (self.repo_text_tab1, self.output_text_tab1):
            self.repo_text_tab1.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif widget in (self.repo_text_tab2, self.output_text_tab2):
            self.repo_text_tab2.yview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            self.main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubRepoInfoGenerator(root)
    root.mainloop()