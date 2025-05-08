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
        self.root.title("GitHub Repo Info Generator")
        self.root.geometry("720x480")
        self.token = None
        self.current_tab = None
        self.include_header = tk.IntVar(value=1)
        self.load_config()
        self.create_widgets()

    def create_widgets(self):
        """创建所有UI组件"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)
        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="无序列表")
        self.notebook.add(self.tab2, text="表格格式")
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        self.create_tab1()
        self.create_tab2()
        self.create_bottom_area()

    def create_tab1(self):
        """创建无序列表标签页"""
        token_frame = ttk.LabelFrame(self.tab1, text="GitHub Personal Access Token (Optional)")
        token_frame.pack(pady=10, padx=10, fill="x")
        self.token_entry = ttk.Entry(token_frame, width=50, show="*")
        self.token_entry.pack(pady=5, padx=5, side="left", expand=True, fill="x")
        if self.token:
            self.token_entry.insert(0, self.token)
        ttk.Button(token_frame, text="设置Token", command=self.set_token).pack(pady=5, padx=5, side="right")

        input_frame = ttk.LabelFrame(self.tab1, text="GitHub Repositories (每行一个 user/repo)")
        input_frame.pack(pady=10, padx=10, fill="both")
        self.repo_text_tab1 = tk.Text(input_frame, width=50, height=5, font=('Consolas', 10))
        self.repo_text_tab1.pack(pady=5, padx=5, side="left", expand=True, fill="both")
        scrollbar = ttk.Scrollbar(input_frame, command=self.repo_text_tab1.yview)
        scrollbar.pack(side="right", fill="y")
        self.repo_text_tab1.config(yscrollcommand=scrollbar.set)

        ttk.Button(input_frame, text="生成", command=lambda: self.threaded_generate('tab1')).pack(pady=5, padx=5, fill="x")

        output_frame = ttk.LabelFrame(self.tab1, text="生成结果 - Markdown 无序列表")
        output_frame.pack(pady=10, padx=10, fill="both", expand=True)
        button_frame = ttk.Frame(output_frame)
        button_frame.pack(pady=5, fill="x")
        ttk.Button(button_frame, text="复制", command=lambda: self.copy_to_clipboard('tab1')).pack(side="right", padx=5)
        self.output_text_tab1 = tk.Text(output_frame, height=12, wrap="word", font=('Consolas', 10))
        self.output_text_tab1.pack(pady=5, padx=5, fill="both", expand=True)

    def create_tab2(self):
        """创建表格格式标签页"""
        input_frame = ttk.LabelFrame(self.tab2, text="GitHub Repositories (每行一个 user/repo)")
        input_frame.pack(pady=10, padx=10, fill="both")
        self.repo_text_tab2 = tk.Text(input_frame, width=50, height=5, font=('Consolas', 10))
        self.repo_text_tab2.pack(pady=5, padx=5, side="left", expand=True, fill="both")
        scrollbar = ttk.Scrollbar(input_frame, command=self.repo_text_tab2.yview)
        scrollbar.pack(side="right", fill="y")
        self.repo_text_tab2.config(yscrollcommand=scrollbar.set)

        control_frame = ttk.Frame(input_frame)
        control_frame.pack(pady=5, fill="x")
        ttk.Checkbutton(control_frame, text="生成表头", variable=self.include_header).pack(side="left", padx=5)
        ttk.Button(control_frame, text="生成", command=lambda: self.threaded_generate('tab2')).pack(side="right", padx=5)

        output_frame = ttk.LabelFrame(self.tab2, text="生成结果 - Markdown 表格")
        output_frame.pack(pady=10, padx=10, fill="both", expand=True)
        button_frame = ttk.Frame(output_frame)
        button_frame.pack(pady=5, fill="x")
        ttk.Button(button_frame, text="复制", command=lambda: self.copy_to_clipboard('tab2')).pack(side="right", padx=5)
        self.output_text_tab2 = tk.Text(output_frame, height=12, wrap="word", font=('Consolas', 10))
        self.output_text_tab2.pack(pady=5, padx=5, fill="both", expand=True)

    def create_bottom_area(self):
        """创建底部区域"""
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def on_tab_change(self, event):
        """切换标签页时更新状态"""
        selected_tab = self.notebook.index(self.notebook.select())
        self.current_tab = 'tab1' if selected_tab == 0 else 'tab2'

    def threaded_generate(self, tab):
        """多线程生成内容"""
        self.clear_output(tab)
        self.set_ui_state(False)
        self.status_var.set("正在获取仓库信息...")
        threading.Thread(target=lambda: self.generate_info(tab), daemon=True).start()

    def generate_info(self, tab):
        """核心生成逻辑（已添加归档检测和最后提交时间）"""
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
                        repo_data = repo_res.json()  # 解析仓库数据
                        
                    except requests.exceptions.HTTPError as e:
                        errors.append(self.handle_http_error(e, repo))
                        continue

                    # 归档状态检测
                    is_archived = repo_data.get('archived', False)
                    if is_archived:
                        # 获取最后一次提交时间
                        pushed_at = repo_data.get('pushed_at', '')
                        if pushed_at:
                            # 格式化为 YYYY-MM-DD 并转义短横线
                            last_commit_date = datetime.strptime(
                                pushed_at, "%Y-%m-%dT%H:%M:%SZ"
                            ).strftime("%Y-%m-%d").replace('-', '--')
                            archived_badge = (
                                f"![Archived](https://img.shields.io/badge/Archived-{last_commit_date}-red?style=flat)"
                            )
                        else:
                            archived_badge = (
                                f"![Archived](https://img.shields.io/badge/Archived-unknown-red?style=flat)"
                            )
                        release_badge = archived_badge
                    else:
                        release_badge = (
                            f"![Latest Release](https://img.shields.io/github/release-date/{user}/{repo_name}?label=Latest+Release&style=flat)"
                        )

                    if tab == 'tab1':
                        link = f"- [{user}/{repo_name}](https://github.com/{user}/{repo_name})"
                        badges = [
                            f"![Stars](https://img.shields.io/github/stars/{user}/{repo_name}?style=flat)",
                            release_badge,
                            f"![Version](https://img.shields.io/github/v/tag/{user}/{repo_name}?label=Version&style=flat)"
                        ]
                        output_lines.append(f"{link}\n  {'  '.join(badges)}\n")
                    else:
                        link = f"[{user}/{repo_name}](https://github.com/{user}/{repo_name})"
                        badges = [
                            f"![Stars](https://img.shields.io/github/stars/{user}/{repo_name}?style=flat)",
                            release_badge,
                            f"![Version](https://img.shields.io/github/v/tag/{user}/{repo_name}?label=Version&style=flat)"
                        ]
                        formatted_badges = '<br>'.join(badges)
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
        """构建最终输出内容"""
        if tab == 'tab1':
            return "\n".join(lines)
        header = "| 项目 | 徽章 | 说明 |\n|------|------|------|\n" if self.include_header.get() else ""
        return header + "\n".join(lines)

    def handle_http_error(self, error, repo):
        """处理HTTP错误"""
        status_code = error.response.status_code
        if status_code == 403:
            return f"API请求次数超限：{repo}（请设置Token）"
        if status_code == 404:
            return f"仓库不存在：{repo}"
        if status_code == 401:
            return f"Token无效：{repo}"
        return f"HTTP错误 {status_code}：{repo}"

    def show_errors(self, errors):
        """显示错误信息"""
        messagebox.showwarning("处理完成但存在错误", "\n".join(errors))
        self.status_var.set(f"生成完成，存在{len(errors)}个错误")

    def set_ui_state(self, enabled):
        """设置界面状态"""
        state = "normal" if enabled else "disabled"
        for tab in ['tab1', 'tab2']:
            getattr(self, f'repo_text_{tab}').config(state=state)
        self.token_entry.config(state=state)
        self.root.config(cursor="" if enabled else "watch")
        self.root.update()

    def clear_output(self, tab):
        """清空输出区域"""
        output_widget = getattr(self, f'output_text_{tab}')
        output_widget.config(state="normal")
        output_widget.delete(1.0, tk.END)
        output_widget.config(state="disabled")

    def update_output(self, content, tab):
        """更新输出内容"""
        output_widget = getattr(self, f'output_text_{tab}')
        output_widget.config(state="normal")
        output_widget.delete(1.0, tk.END)
        output_widget.insert(tk.END, content)
        output_widget.config(state="disabled")

    def copy_to_clipboard(self, tab):
        """复制输出内容到剪贴板"""
        output_widget = getattr(self, f'output_text_{tab}')
        text = output_widget.get(1.0, tk.END).strip()
        if text:
            pyperclip.copy(text)
            self.status_var.set("内容已复制到剪贴板")

    def show_error(self, message):
        """显示错误弹窗"""
        messagebox.showerror("错误", message)
        self.status_var.set(message)

    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r') as f:
                    self.token = json.load(f).get('token')
        except Exception as e:
            self.show_error(f"加载配置失败: {str(e)}")

    def save_config(self):
        """保存配置文件"""
        try:
            os.makedirs(self.CONFIG_DIR, exist_ok=True)
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump({'token': self.token}, f)
            if os.name != 'nt':
                os.chmod(self.CONFIG_FILE, 0o600)
        except Exception as e:
            self.show_error(f"保存配置失败: {str(e)}")

    def set_token(self):
        """设置GitHub Token"""
        new_token = self.token_entry.get().strip()
        if new_token != self.token:
            self.token = new_token or None
            self.save_config()
            self.status_var.set(f"Token {'已更新' if self.token else '已清除'}")
        else:
            self.status_var.set("Token未变化")

if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubRepoInfoGenerator(root)
    root.mainloop()