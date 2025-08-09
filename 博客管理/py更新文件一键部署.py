import os
import subprocess
import time
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

class DeployHelper:
    def __init__(self, parent):
        self.parent = parent
        self.repo_path = os.getcwd()  # Ĭ�ϵ�ǰĿ¼
        self.remote_repo = ""
        self.branch = "main"
        
    def set_repo_info(self, repo_path, remote_repo, branch):
        """���òֿ���Ϣ"""
        self.repo_path = repo_path
        self.remote_repo = remote_repo
        self.branch = branch or "main"
    
    def run_deploy(self):
        """ִ�в�������"""
        # ��ȡ����˵��
        msg = simpledialog.askstring(
            "����˵��", 
            "���������˵����",
            parent=self.parent,
            initialvalue=f"update: {time.strftime('%Y-%m-%d %H:%M')}"
        )
        
        if msg is None:  # �û�ȡ��
            return False
            
        if not msg.strip():
            msg = f"update: {time.strftime('%Y-%m-%d')}"
        
        # ��ʾ������ȴ���
        progress_window = tk.Toplevel(self.parent)
        progress_window.title("���ڲ���")
        progress_window.geometry("500x300")
        progress_window.transient(self.parent)
        progress_window.grab_set()
        
        # ������
        ttk.Label(progress_window, text="������ȣ�").pack(pady=10, anchor=tk.W, padx=20)
        progress = ttk.Progressbar(progress_window, length=450, mode='indeterminate')
        progress.pack(pady=10)
        progress.start()
        
        # ��־����
        ttk.Label(progress_window, text="������־��").pack(pady=10, anchor=tk.W, padx=20)
        log_text = tk.Text(progress_window, height=8, wrap=tk.WORD)
        log_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        log_scroll = ttk.Scrollbar(log_text, command=log_text.yview)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        log_text.config(yscrollcommand=log_scroll.set, state=tk.DISABLED)
        
        # ������־�ĺ���
        def update_log(message):
            log_text.config(state=tk.NORMAL)
            log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
            log_text.see(tk.END)
            log_text.config(state=tk.DISABLED)
            progress_window.update_idletasks()
        
        # �����߳���ִ�в�������
        result = [False]  # ���б�洢������Ա����ڲ��������޸�
        
        def deploy_thread():
            try:
                # ����Ƿ���Git�ֿ�
                if not os.path.exists(os.path.join(self.repo_path, ".git")):
                    update_log("δ����Git�ֿ⣬���ڳ�ʼ��...")
                    self.run_command("git init", update_log)
                
                # ���Զ�ֿ̲�����
                if self.remote_repo:
                    remotes = self.run_command("git remote", update_log, capture_output=True)
                    if "origin" not in remotes:
                        update_log(f"���Զ�ֿ̲�: {self.remote_repo}")
                        self.run_command(f"git remote add origin {self.remote_repo}", update_log)
                    else:
                        # ���Զ�ֿ̲��Ƿ�ƥ��
                        current_remote = self.run_command("git remote get-url origin", update_log, capture_output=True)
                        if current_remote.strip() != self.remote_repo.strip():
                            update_log(f"����Զ�ֿ̲��ַΪ: {self.remote_repo}")
                            self.run_command(f"git remote set-url origin {self.remote_repo}", update_log)
                
                # ����֧
                branches = self.run_command("git branch --list", update_log, capture_output=True)
                if f"*{self.branch}" not in branches and self.branch not in branches:
                    update_log(f"�������л��� {self.branch} ��֧")
                    self.run_command(f"git checkout -b {self.branch}", update_log)
                else:
                    update_log(f"�л��� {self.branch} ��֧")
                    self.run_command(f"git checkout {self.branch}", update_log)
                
                # ��ȡ���´���
                update_log("��ȡԶ�����´���...")
                self.run_command(f"git pull origin {self.branch}", update_log, allow_failure=True)
                
                # ����ļ�
                update_log("����ļ����ݴ���...")
                self.run_command("git add .", update_log)
                
                # �ύ����
                update_log(f"�ύ����: {msg}")
                self.run_command(f'git commit -m "{msg}"', update_log, allow_failure=True)
                
                # ���͸���
                update_log("���͸��ĵ�Զ�ֿ̲�...")
                self.run_command(f"git push origin {self.branch}", update_log)
                
                update_log("������ɣ�")
                result[0] = True
                
            except Exception as e:
                update_log(f"����ʧ��: {str(e)}")
            finally:
                progress.stop()
                ttk.Button(progress_window, text="�ر�", command=progress_window.destroy).pack(pady=10)
        
        # ���������߳�
        import threading
        threading.Thread(target=deploy_thread, daemon=True).start()
        
        progress_window.wait_window()  # �ȴ����ڹر�
        return result[0]
    
    def run_command(self, command, log_callback, capture_output=False, allow_failure=False):
        """ִ������������"""
        try:
            # ִ������
            process = subprocess.Popen(
                command,
                cwd=self.repo_path,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding="utf-8",
                errors="replace"  # ����������
            )
            
            # ʵʱ�����־
            output = []
            for line in process.stdout:
                stripped_line = line.strip()
                if stripped_line:
                    log_callback(stripped_line)
                    output.append(stripped_line)
            
            process.wait()
            
            # ��鷵�ش���
            if process.returncode != 0 and not allow_failure:
                raise Exception(f"����ִ��ʧ��: {command} (���ش���: {process.returncode})")
                
            return "\n".join(output) if capture_output else None
            
        except Exception as e:
            log_callback(f"����ִ�д���: {str(e)}")
            if not allow_failure:
                raise
            return None

# ��������ʱ�Ĳ��Դ���
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # ����������
    
    deployer = DeployHelper(root)
    
    # ��ȡ�ֿ�·��
    repo_path = simpledialog.askstring(
        "�ֿ�·��", 
        "�����벩�Ͳֿ�·����",
        initialvalue=os.getcwd()
    )
    
    if repo_path and os.path.exists(repo_path):
        deployer.set_repo_info(
            repo_path,
            simpledialog.askstring("Զ�ֿ̲�", "������Զ�ֿ̲��ַ��"),
            simpledialog.askstring("��֧", "�������֧���ƣ�", initialvalue="main")
        )
        
        success = deployer.run_deploy()
        if success:
            messagebox.showinfo("�ɹ�", "������ɣ������Ӻ�ˢ����ҳ���ɿ������¡�")
        else:
            messagebox.showerror("ʧ��", "��������г��ִ�����鿴��־��")
    else:
        messagebox.showerror("����", "��Ч�Ĳֿ�·��")
    
    root.destroy()
