import requests
import tkinter as tk
from tkinter import ttk, messagebox
import pyperclip
import os
import json
import threading
import logging
from functools import partial

# 配置日志记录
logging.basicConfig(filename='app.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class GitHubRepoInfoGenerator:
    CONFIG_DIR = os.path.expanduser("~/.config/gh_repo_info")
    CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
    
    STRINGS = {
        'token_label': "GitHub Personal Access Token (Optional)",
        'generate_btn': "生成",
        'copy_btn': "复制结果",
        'status_generating': "正在获取仓库信息...",
        'error_init': "程序初始化失败"
    }

    def __init__(self, root):
        try:
            self.root = root
            self.root.title("GitHub Repo Info Generator")
            self.root.geometry("800x520")
            self.root.minsize(720, 480)
            
            self.token = None
            self.current_tab = None
            self.include_header = tk.IntVar(value=1)
            self.rate_limit_remaining = -1
            self.cache = {}
            
            self.setup_config_dir()
            self.load_config()
            self.create_widgets()
        except Exception as e:
            logging.exception(self.STRINGS['error_init'])
            tk.messagebox.showerror("致命错误", f"{self.STRINGS['error_init']}: {str(e)}")
            root.destroy()

    def setup_config_dir(self):
        try:
            os.makedirs(self.CONFIG_DIR, exist_ok=True)
            if os.name != 'nt':
                os.chmod(self.CONFIG_DIR, 0o700)
        except Exception as e:
            self.show_error(f"创建配置目录失败: {str(e)}")

    def create_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.tab1 = self.create_tab_frame("无序列表")
        self.tab2 = self.create_tab_frame("表格格式")
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        
        self.create_tab1_content()
        self.create_tab2_content()
        self.create_bottom_area()

    # 新增关键方法：处理标签页切换事件
    def on_tab_change(self, event):
        """切换标签页时更新当前标签状态"""
        selected_tab = self.notebook.index(self.notebook.select())
        self.current_tab = 'tab1' if selected_tab == 0 else 'tab2'

    def create_tab_frame(self, text):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=text)
        return frame

    def create_common_input_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="GitHub Repositories (每行一个 user/repo)")
        frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        text_widget = tk.Text(frame, width=50, height=5, font=('Consolas', 10))
        scrollbar = ttk.Scrollbar(frame, command=text_widget.yview)
        text_widget.config(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
        return text_widget

    def create_tab1_content(self):
        token_frame = ttk.LabelFrame(self.tab1, text=self.STRINGS['token_label'])
        token_frame.pack(pady=5, padx=10, fill="x")
        
        self.token_entry = ttk.Entry(token_frame, width=50, show="*")
        self.token_entry.pack(pady=5, padx=5, side="left", expand=True, fill="x")
        if self.token:
            self.token_entry.insert(0, self.token)
        ttk.Button(token_frame, text="设置Token", command=self.set_token).pack(side="right", padx=5)
        
        self.repo_text_tab1 = self.create_common_input_frame(self.tab1)
        ttk.Button(self.tab1, text=self.STRINGS['generate_btn'], 
                 command=partial(self.threaded_generate, 'tab1')).pack(pady=5)
        
        output_frame = ttk.LabelFrame(self.tab1, text="生成结果 - Markdown 无序列表")
        output_frame.pack(pady=10, padx=10, fill="both", expand=True)
        self.output_text_tab1 = self.create_output_widget(output_frame, 'tab1')

    def create_tab2_content(self):
        self.repo_text_tab2 = self.create_common_input_frame(self.tab2)
        
        control_frame = ttk.Frame(self.tab2)
        control_frame.pack(pady=5)
        ttk.Checkbutton(control_frame, text="生成表头", variable=self.include_header).pack(side="left", padx=5)
        ttk.Button(control_frame, text=self.STRINGS['generate_btn'], 
                 command=partial(self.threaded_generate, 'tab2')).pack(side="right", padx=5)
        
        output_frame = ttk.LabelFrame(self.tab2, text="生成结果 - Markdown 表格")
        output_frame.pack(pady=10, padx=10, fill="both", expand=True)
        self.output_text_tab2 = self.create_output_widget(output_frame, 'tab2')

    def create_output_widget(self, parent, tab):
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=5, fill="x")
        ttk.Button(button_frame, text=self.STRINGS['copy_btn'], 
                 command=partial(self.copy_to_clipboard, tab)).pack(side="right", padx=5)
        
        text_widget = tk.Text(parent, height=12, wrap="word", font=('Consolas', 10))
        text_widget.pack(pady=5, padx=5, fill="both", expand=True)
        return text_widget

    def create_bottom_area(self):
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=2)
        
        rate_limit_frame = ttk.Frame(self.root)
        rate_limit_frame.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Label(rate_limit_frame, text="API剩余次数:").pack(side="left")
        self.rate_limit_label = ttk.Label(rate_limit_frame, text="N/A")
        self.rate_limit_label.pack(side="left", padx=5)

    def threaded_generate(self, tab):
        self.clear_output(tab)
        self.set_ui_state(False)
        self.status_var.set(self.STRINGS['status_generating'])
        threading.Thread(target=lambda: self.generate_info(tab), daemon=True).start()

    def generate_info(self, tab):
        errors = []
        output_lines = []
        try:
            inputs = getattr(self, f'repo_text_{tab}').get("1.0", tk.END).strip().splitlines()
            valid_repos = []
            for repo in inputs:
                repo = repo.strip()
                if not repo:
                    continue
                if repo.count("/") != 1:
                    errors.append(f"无效的仓库格式: {repo}")
                    continue
                valid_repos.append(repo)

            if not valid_repos:
                self.show_errors(errors or ["未输入有效仓库地址"])
                return

            headers = {"Authorization": f"token {self.token}"} if self.token else {}
            session = requests.Session()
            session.headers.update(headers)

            for repo in valid_repos:
                user, repo_name = repo.split("/", 1)
                cache_key = f"{user}/{repo_name}"
                
                if cache_key in self.cache:
                    repo_data = self.cache[cache_key]
                else:
                    try:
                        repo_res = session.get(
                            f"https://api.github.com/repos/{user}/{repo_name}",
                            headers=headers
                        )
                        self.update_rate_limit(repo_res.headers)
                        repo_res.raise_for_status()
                        repo_data = repo_res.json()
                        self.cache[cache_key] = repo_data
                    except requests.exceptions.HTTPError as e:
                        error_msg = self.handle_http_error(e, repo)
                        errors.append(error_msg)
                        logging.error(f"HTTP Error: {error_msg}")
                        continue
                    except Exception as e:
                        errors.append(f"请求失败: {repo} - {str(e)}")
                        logging.exception(f"请求异常: {repo}")
                        continue

                try:
                    if tab == 'tab1':
                        link = f"- [{user}/{repo_name}](https://github.com/{user}/{repo_name})"
                        badges = [
                            f"![Stars](https://img.shields.io/github/stars/{user}/{repo_name}?style=flat)",
                            f"![Latest Release](https://img.shields.io/github/release-date/{user}/{repo_name}?label=Latest+Release&style=flat)",
                            f"![Version](https://img.shields.io/github/v/tag/{user}/{repo_name}?label=Version&style=flat)"
                        ]
                        output_lines.append(f"{link}\n\n  {'  '.join(badges)}\n")
                    else:
                        link = f"[{user}/{repo_name}](https://github.com/{user}/{repo_name})"
                        badges = [
                            f"![Stars](https://img.shields.io/github/stars/{user}/{repo_name}?style=flat)",
                            f"![Latest Release](https://img.shields.io/github/release-date/{user}/{repo_name}?label=Latest+Release&style=flat)",
                            f"![Version](https://img.shields.io/github/v/tag/{user}/{repo_name}?label=Version&style=flat)"
                        ]
                        formatted_badges = '<br>'.join(badges)
                        output_lines.append(f"| {link} | {formatted_badges} |  |")
                except KeyError as e:
                    errors.append(f"解析仓库数据失败: {repo} - 缺少字段 {str(e)}")
                    logging.error(f"数据解析错误: {repo} - {str(e)}")

            md_content = self.build_output(tab, output_lines)
            self.root.after(0, self.update_output, md_content, tab)
            self.root.after(0, self.update_status, "生成成功", errors)
            
        except Exception as e:
            logging.exception("生成过程发生未捕获异常")
            self.root.after(0, self.show_error, f"严重错误: {str(e)}")
        finally:
            self.root.after(0, self.set_ui_state, True)

    def update_rate_limit(self, headers):
        remaining = headers.get('X-RateLimit-Remaining', 'N/A')
        self.rate_limit_remaining = remaining
        self.root.after(0, lambda: self.rate_limit_label.config(text=str(remaining)))

    def build_output(self, tab, lines):
        if not lines:
            return ""
        if tab == 'tab1':
            return "\n".join(lines)
        header = "| 项目 | 徽章 | 说明 |\n|------|------|------|\n" if self.include_header.get() else ""
        return header + "\n".join(lines)

    def copy_to_clipboard(self, tab):
        try:
            output_widget = getattr(self, f'output_text_{tab}')
            text = output_widget.get("1.0", tk.END).strip()
            if text:
                pyperclip.copy(text)
                self.status_var.set("内容已复制到剪贴板")
        except pyperclip.PyperclipException as e:
            self.show_error(f"复制失败: {str(e)}")
            logging.error(f"剪贴板错误: {str(e)}")
        except AttributeError as e:
            self.show_error(f"组件访问错误: {str(e)}")
            logging.error(f"组件错误: {str(e)}")

    def update_status(self, message, errors=None):
        if errors:
            self.show_errors(errors)
            self.status_var.set(f"{message}，存在{len(errors)}个错误")
        else:
            self.status_var.set(message)

    def set_ui_state(self, enabled):
        state = "normal" if enabled else "disabled"
        self.root.config(cursor="" if enabled else "watch")
        for widget in [self.repo_text_tab1, self.repo_text_tab2, self.token_entry]:
            widget.config(state=state)

    def show_error(self, message):
        messagebox.showerror("错误", message)
        self.status_var.set(message)

    def load_config(self):
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r') as f:
                    self.token = json.load(f).get('token')
        except Exception as e:
            self.show_error(f"加载配置失败: {str(e)}")

    def save_config(self):
        try:
            os.makedirs(self.CONFIG_DIR, exist_ok=True)
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump({'token': self.token}, f)
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

if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubRepoInfoGenerator(root)
    root.mainloop()