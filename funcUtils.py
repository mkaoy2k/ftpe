import os
from dotenv import load_dotenv  # pip install python-dotenv
import json
import streamlit as st  # pip install streamlit
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl
import smtplib
import tempfile

def load_menu(fn):
    """
    讀取菜單設定檔
    
    參數:
        fn (str): 設定檔路徑
    
    回傳:
        dict: 設定檔內容
    """
    with open(fn) as f:
        data = f.read()
    return json.loads(data)


@st.cache_data(ttl=300)
def load_L10N(base=None):
    """
    載入支援的本地化字典
    
    參數:
        base (str, optional): 基準目錄
    
    回傳:
        dict: 包含所有支援語言的本地化字典
    """
    load_dotenv(".env")
    f_l10n = os.getenv("L10N_FILE")
    
    with open(f_l10n) as f:
        data = f.read()
    js = json.loads(data)
    
    dl10n = {}
    for key, fl in js.items():
        with open(fl) as f:
            data = f.read()
        d = json.loads(data)
        dl10n[key] = d
    
    return dl10n


def send_email(someone, subject=None, f_text=None, f_html=None, f_attached=None):
    """
    透過 Google 電子郵件帳號發送郵件
    
    參數:
        someone (str): 收件人電子郵件
        subject (str, optional): 郵件主題
        f_text (str, optional): 文本檔案路徑
        f_html (str, optional): HTML 檔案路徑
        f_attached (str, optional): 附件檔案路徑
    
    前置條件:
        1. 需要設定發件人的 Google 電子郵件帳號
            1) 開啟兩步驗證
            2) 建立應用程式密碼
    """
    load_dotenv(".env")
    email_password = os.getenv("EMAIL_PW")
    email_sender = os.getenv("EMAIL_SENDER")
    
    em = MIMEMultipart("alternative")
    em['From'] = email_sender
    em['To'] = someone
    em['Subject'] = subject

    # 設定郵件內容
    if f_text:
        with open(f_text, 'r') as f:
            text = f.read()
        if subject is None:
            subject = f'The Contents of {f_text}'
    else:
        text = "Empty Text"
    
    part1 = MIMEText(text, "plain")
    em.attach(part1)

    if f_html:
        with open(f_html, 'r') as f:
            html = f.read()
        if subject is None:
            subject = f'The Contents of {f_html}'
    else:
        html = "<html><body><h1>Empty HTML</h1></body></html>"
    
    part2 = MIMEText(html, "html")
    em.attach(part2)

    if f_attached:
        with open(f_attached, "rb") as attachment:
            part3 = MIMEBase("application", "octet-stream")
            part3.set_payload(attachment.read())
        
        encoders.encode_base64(part3)
        part3.add_header("Content-Disposition", "attachment", filename=f_attached)
        em.attach(part3)
        
    # 發送郵件
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, someone, em.as_string())


def verify_email(email, subject, action, msg, template=None):
    """
    建立並發送驗證電子郵件
    
    參數:
        email (str): 收件人電子郵件
        subject (str): 郵件主題
        action (str): 行動連結
        msg (str): 郵件內容
        template (str, optional): 模板檔案路徑
    """
    with tempfile.NamedTemporaryFile(mode='w+t') as fc:
        fc.writelines(f"<html><body><h1>{subject}</h1>")
        fc.writelines(action)
        fc.writelines(msg)
        
        if template:
            with open(template, 'r') as f:
                fc.writelines(f.read())
        
        fc.seek(0)
        send_email(email,
                   subject=f"{subject}, please confirm from FamilyTrees!",
                   f_html=fc.name)


@st.cache_data(ttl=300)
def get_1st_mbr_dict(df, mem, born, base=None):
    """
    在 DataFrame 中查找第一筆符合條件的成員記錄
    
    參數:
        df (pd.DataFrame): 資料框
        mem (str): 成員姓名
        born (int): 出生年份
        base (str, optional): 基準目錄
    
    回傳:
        tuple: (index, member_dict)
            index: 記錄索引
            member_dict: 成員資料字典
    
    異常:
        FileNotFoundError: 如果找不到符合條件的記錄
    """
    filter = f"Name == @mem and Born == @born"
    try:
        rec = df.query(filter)
        if rec.empty:
            raise FileNotFoundError("找不到符合條件的記錄")
    except Exception as e:
        raise
    
    # 移除重複記錄，只保留第一筆
    rec = rec[0:1]
    idx, member = rec.to_dict('index').popitem()
    return idx, member


if __name__ == '__main__':
    """
    功能測試代碼
    """
    path_dir = 'data'  # 相對於當前目錄
    email_receiver = "mkaoy2k@yahoo.com"
    confirm_template = f"{path_dir}/confirm.html"
    email_text = f'{path_dir}/template.txt'
    email_html = f'{path_dir}/template.html'
    email_attached = f'{path_dir}/template.png'

    try:
        verify_email(email_receiver, # receiver
            "Henry Kao",      # full name
            "hkao",             # username
            "abc123",           # msg
            confirm_template,   # template
            )
        print(f"confirmation successfully sent, check {email_receiver}")   
                            
    except Exception as err:
        print(f"Caught '{err}'. class is {type(err)}")
        print(f"send confirm email failed")    
