import requests
import tkinter as tk
from tkinter import ttk, messagebox
import pyperclip
import os
import json
import threading

class GitHubRepoInfoGenerator:
    CONFIG_DIR = os.path.expanduser("~/.config/gh_repo_info")
    CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

    def __init__(self, root):
        self.root = root
        self.root.title("GitHub Repo Info Generator")
        self.root.geometry("720x480")
        
        self.token = None
        self.load_config()
        self.create_widgets()

    def create_widgets(self):
        """创建所有UI组件"""
        # Token输入区域
        token_frame = ttk.LabelFrame(self.root, text="GitHub Personal Access Token (Optional)")
        token_frame.pack(pady=10, padx=10, fill="x")
        
        self.token_entry = ttk.Entry(token_frame, width=50, show="*")
        self.token_entry.pack(pady=5, padx=5, side="left", expand=True, fill="x")
        
        if self.token:
            self.token_entry.insert(0, self.token)
        
        ttk.Button(token_frame, text="Set Token", command=self.set_token).pack(pady=5, padx=5, side="right")
        
        # 仓库输入区域
        input_frame = ttk.LabelFrame(self.root, text="GitHub Repository (user/repo)")
        input_frame.pack(pady=10, padx=10, fill="x")
        
        self.repo_entry = ttk.Entry(input_frame, width=50)
        self.repo_entry.pack(pady=5, padx=5, side="left", expand=True, fill="x")
        
        ttk.Button(input_frame, text="Generate", command=self.threaded_generate).pack(pady=5, padx=5, side="right")
        
        # 输出区域
        output_frame = ttk.LabelFrame(self.root, text="Output - Markdown Format")
        output_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        self.output_text = tk.Text(output_frame, height=12, wrap="word", font=('Consolas', 10))
        self.output_text.pack(pady=5, padx=5, fill="both", expand=True)
        
        # 状态栏
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 复制按钮
        ttk.Button(self.root, text="复制", command=self.copy_to_clipboard).pack(pady=5)

    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.token = config.get('token')
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
        """设置并保存Token"""
        new_token = self.token_entry.get().strip()
        if new_token != self.token:
            self.token = new_token or None
            self.save_config()
            status = "已更新" if self.token else "已清除"
            self.status_var.set(f"Token {status}")
        else:
            self.status_var.set("Token未变化")

    def threaded_generate(self):
        """启动生成线程"""
        self.clear_output()
        self.set_ui_state(False)
        self.status_var.set("正在获取仓库信息...")
        threading.Thread(target=self.generate_info, daemon=True).start()

    def generate_info(self):
        """主生成逻辑"""
        try:
            repo_input = self.repo_entry.get().strip()
            if not self.validate_input(repo_input):
                return

            user, repo = repo_input.split("/", 1)
            headers = {"Authorization": f"token {self.token}"} if self.token else {}
            
            # 验证仓库存在性
            with requests.Session() as session:
                session.timeout = 10
                try:
                    repo_res = session.get(
                        f"https://api.github.com/repos/{user}/{repo}",
                        headers=headers
                    )
                    repo_res.raise_for_status()
                except requests.exceptions.HTTPError as e:
                    self.handle_http_error(e, "仓库验证失败")
                    return

                # 生成动态徽章
                md_content = self.build_markdown(user, repo)
                self.update_output(md_content)
                self.status_var.set("生成成功")

        except Exception as e:
            self.show_error(f"生成过程中发生异常: {str(e)}")
        finally:
            self.set_ui_state(True)

    def build_markdown(self, user, repo):
        """构建Markdown内容（使用动态徽章）"""
        md_link = f"[{user}/{repo}](https://github.com/{user}/{repo})"
        stars_badge = f"![Stars](https://img.shields.io/github/stars/{user}/{repo}?style=flat)"
        # 使用tags代替release获取更干净的版本号
        version_badge = f"![Version](https://img.shields.io/github/v/tag/{user}/{repo}?label=Version&style=flat)"
        release_badge = f"![Release Date](https://img.shields.io/github/release-date/{user}/{repo}?label=Latest+Release&style=flat)"
            
        return f"{md_link} {stars_badge}\n\n{release_badge} {version_badge}"

    def validate_input(self, repo_input):
        """输入验证"""
        if not repo_input:
            self.show_error("请输入仓库名称")
            return False
        if "/" not in repo_input:
            self.show_error("格式错误，请使用 user/repo 格式")
            return False
        return True

    def set_ui_state(self, enabled):
        """更新界面状态"""
        state = "normal" if enabled else "disabled"
        for widget in [self.token_entry, self.repo_entry]:
            widget.config(state=state)
        self.root.config(cursor="" if enabled else "watch")
        self.root.update()

    def clear_output(self):
        """清空输出"""
        self.output_text.delete(1.0, tk.END)

    def update_output(self, content):
        """更新输出内容"""
        self.output_text.config(state="normal")
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, content)
        self.output_text.config(state="disabled")

    def handle_http_error(self, error, context):
        """处理HTTP错误"""
        status_code = error.response.status_code
        if status_code == 403:
            msg = f"{context}：API请求次数超限，请设置Token"
        elif status_code == 404:
            msg = f"{context}：仓库不存在"
        elif status_code == 401:
            msg = f"{context}：Token无效"
        else:
            msg = f"{context}：HTTP错误 {status_code}"
        self.show_error(msg)

    def show_error(self, message):
        """显示错误"""
        self.status_var.set(message)
        messagebox.showerror("错误", message)

    def copy_to_clipboard(self):
        """复制到剪贴板"""
        text = self.output_text.get(1.0, tk.END).strip()
        if text:
            pyperclip.copy(text)
            self.status_var.set("内容已复制到剪贴板")

if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubRepoInfoGenerator(root)
    root.mainloop()