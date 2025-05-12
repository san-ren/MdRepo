import requests
import tkinter as tk
from tkinter import ttk, messagebox
import pyperclip

class GitHubRepoInfoGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub Repo Info Generator")
        self.root.geometry("720x480")
        
        self.token = None
        self.create_widgets()
        
    def create_widgets(self):
        # 令牌输入区域
        token_frame = ttk.LabelFrame(self.root, text="GitHub Personal Access Token (Optional)")
        token_frame.pack(pady=10, padx=10, fill="x")
        
        self.token_entry = ttk.Entry(token_frame, width=50, show="*")
        self.token_entry.pack(pady=5, padx=5, side="left", expand=True, fill="x")
        
        ttk.Button(token_frame, text="Set Token", command=self.set_token).pack(pady=5, padx=5, side="right")
        
        # 仓库输入区域
        input_frame = ttk.LabelFrame(self.root, text="GitHub Repository (user/repo)")
        input_frame.pack(pady=10, padx=10, fill="x")
        
        self.repo_entry = ttk.Entry(input_frame, width=50)
        self.repo_entry.pack(pady=5, padx=5, side="left", expand=True, fill="x")
        
        ttk.Button(input_frame, text="Generate", command=self.generate_info).pack(pady=5, padx=5, side="right")
        
        # 输出区域
        output_frame = ttk.LabelFrame(self.root, text="Output - Markdown Format")
        output_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        self.output_text = tk.Text(output_frame, height=12, wrap="word", font=('Consolas', 10))
        self.output_text.pack(pady=5, padx=5, fill="both", expand=True)
        
        ttk.Button(self.root, text="Copy to Clipboard", command=self.copy_to_clipboard).pack(pady=5)
    
    def set_token(self):
        self.token = self.token_entry.get()
        messagebox.showinfo("Info", "Token updated!" if self.token else "Token cleared")
    
    def generate_info(self):
        repo_input = self.repo_entry.get().strip()
        if not repo_input or '/' not in repo_input:
            messagebox.showerror("Error", "请输入 user/repo 格式的仓库名")
            return
            
        user, repo = repo_input.split("/", 1)
        self.output_text.delete(1.0, tk.END)
        self.root.config(cursor="watch")
        self.root.update()
        
        try:
            headers = {"Authorization": f"token {self.token}"} if self.token else {}
            
            with requests.Session() as session:
                # 验证仓库存在性
                repo_url = f"https://api.github.com/repos/{user}/{repo}"
                repo_res = session.get(repo_url, headers=headers)
                
                if repo_res.status_code == 404:
                    messagebox.showerror("错误", "仓库不存在")
                    return
                repo_res.raise_for_status()
                
                # 获取stars信息
                stars = repo_res.json().get('stargazers_count', 'N/A')
                
                # 生成基础徽章
                md_link = f"[{user}/{repo}](https://github.com/{user}/{repo})"
                stars_badge = f"![Stars](https://img.shields.io/github/stars/{user}/{repo}?label=Stars&style=flat)"
                
                # 智能生成版本信息
                version_badge = self.get_version_badge(session, user, repo, headers)
                release_badge = self.get_release_badge(user, repo)
                
                output = f"{md_link} {stars_badge}\n\n{release_badge} {version_badge}"
                self.output_text.insert(tk.END, output)
                
        except requests.exceptions.HTTPError as e:
            self.handle_http_error(e)
        except Exception as e:
            messagebox.showerror("错误", f"发生未知错误: {str(e)}")
        finally:
            self.root.config(cursor="")
    
    def get_version_badge(self, session, user, repo, headers):
        """智能获取版本信息"""
        try:
            # 尝试获取最新release
            release_res = session.get(
                f"https://api.github.com/repos/{user}/{repo}/releases/latest",
                headers=headers
            )
            if release_res.status_code == 200:
                version = release_res.json().get('tag_name', 'N/A')
                if version.startswith('v'):
                    version = version[1:]
                return f"![Version](https://img.shields.io/badge/version-{version}-blue?style=flat)"
            
            # 没有release则尝试获取最新tag
            tags_res = session.get(
                f"https://api.github.com/repos/{user}/{repo}/tags",
                headers=headers
            )
            if tags_res.status_code == 200 and tags_res.json():
                version = tags_res.json()[0]['name']
                if version.startswith('v'):
                    version = version[1:]
                return f"![Version](https://img.shields.io/badge/version-{version}-blue?style=flat)"
                
        except:
            pass
        
        # 没有版本信息时显示提示
        return "![Version](https://img.shields.io/badge/version-no_releases-lightgrey?style=flat)"
    
    def get_release_badge(self, user, repo):
        """动态发布日期徽章"""
        return f"![Release](https://img.shields.io/github/release-date/{user}/{repo}?label=last_release&style=flat)"
    
    def handle_http_error(self, e):
        """处理HTTP错误"""
        status_code = e.response.status_code
        if status_code == 403:
            msg = "API请求次数超限，请设置Personal Access Token"
        elif status_code == 401:
            msg = "Token无效，请重新设置"
        elif status_code == 404:
            msg = "仓库不存在"
        else:
            msg = f"API请求失败: {str(e)}"
        messagebox.showerror("API错误", msg)
    
    def copy_to_clipboard(self):
        """静默复制到剪贴板"""
        text = self.output_text.get(1.0, tk.END).strip()
        if text:
            pyperclip.copy(text)

if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubRepoInfoGenerator(root)
    root.mainloop()