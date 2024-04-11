
import os
from dotenv import load_dotenv  # pip install python-dotenv
import json
import streamlit as st  # pip install streamlit

# Import email packages
import email
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl

# Using 'smtplib' module to create an SMTP client session object 
# that sends an email to any SMTP server
import smtplib

# Tempory file module
import tempfile

def load_menu(fn):

    # reading the data from the language-definition file
    with open(fn) as f:
        data = f.read()
        
    # reconstructing languages as a dictionary
    js = json.loads(data)
    
    return js

# --- Load supported L10N dictionaries ---
@st.cache_data(ttl=300)
def load_L10N(base=None):
    # Build and return a dictionary for all supported languages, 
    # with key of language name and associated L10N dictionaries.
    # Load the environment variables from file
    load_dotenv(".env")
    f_l10n = os.getenv("L10N_FILE")

    # reading the data from the language-definition file
    with open(f_l10n) as f:
        data = f.read()
        
    # reconstructing languages as a dictionary
    js = json.loads(data)
    
    dl10n = {}
    # iterate all supported languages
    for key, fl in js.items():
        # load each language-specific L10N settings
        with open(fl) as f:
            data = f.read()
      
        # reconstructing the data as a dictionary
        d = json.loads(data)
        dl10n[key] = d
  
    return dl10n

# send file(s) to someone 
def send_email(someone, subject=None, 
               f_text=None, 
               f_html=None, 
               f_attached=None):
    """ 
    This function to send an email via Google email account
    with plain text and alternative html parts.
    Pre-requisites:
    1. Need to configure your sender Google email account with
        1) two-step confirmation
        2) create an app password
    """
    email_receiver = someone
    # Load the environment variables from file
    load_dotenv(".env")
    
    # Load the environment variable for logging
    email_password = os.getenv("EMAIL_PW")
    email_sender = os.getenv("EMAIL_SENDER")
    em = MIMEMultipart("alternative")
    em['From'] = email_sender
    em['To'] = email_receiver
    em['Subject'] = subject

    # Compose the email object combines these into a signle 
    # email message with two alternative rendering options.
    # Add plain and html parts to MIMEMultipart message
    # The recipiant client will try to render the last part first

    if f_text:
        with open(f_text, 'r') as f:
            text = f.read()
        if subject == None:
            subject = f'The Contents of {f_text}'
    else:
        text = "Empty Text"
    
    # Compose Text part
    part1 = MIMEText(text, "plain")
    em.attach(part1)

    if f_html:
        with open(f_html, 'r') as f:
            html = f.read()
        if subject == None:
            subject = f'The Contents of {f_html}'
    else:
        html = "<html><body><h1>Empty HTML</h1></body></html>"
        
    # Compose HTML part
    part2 = MIMEText(html, "html")
    em.attach(part2)

    if f_attached:
        # Add attachment
        with open(f_attached, "rb") as attachment:
            part3 = MIMEBase("application", "octet-stream")
            part3.set_payload(attachment.read())

        # encode the above part
        encoders.encode_base64(part3)

        # Add specific content header to the attachment
        part3.add_header("Content-Disposition", "attachment", 
                         filename=f_attached)
        em.attach(part3)
        
    # Create SMTP connection
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_password)

        # Send out the email
        try:
            smtp.sendmail(email_sender, email_receiver, em.as_string())

        except Exception as err:
            raise(err)
    return

def verify_email(email, subject, action, msg, template=None):
    # create a verification email to new applicant
    # The email has 3 parts: header (greeting), action (link attached)
    # and the best wishes.
    fc = tempfile.NamedTemporaryFile(mode='w+t')
    header = f"<html><body><h1>{subject}</h1>"
    fc.writelines(header)
    fc.writelines(action)
    fc.writelines(msg)
                
    if template:
        with open(template, 'r') as f:
            temp_contents = f.read()

            fc.writelines(temp_contents)
    fc.seek(0)
    
    # send the verification via email
    send_email(email,
            subject=f"{subject}, please confirm from FamilyTrees!",
            f_html=fc.name,
            )

    fc.close()        
    return

def get_1st_mbr_dict(df, mem, born):
    """
    Return an index and associated dict obj, containing the FIRST record 
    found in 'df' dataframe, matching given member-name and birth-year.
    
    Raise 'FileNotFoundError' if not found, otherwise.
    """
    # log.debug(f"Filter = 'Name == {mem} and Born = {born}'")
    filter = f"Name == @mem and Born == @born"
    try:
        rec = df.query(filter)
        if rec.empty:
            raise(FileNotFoundError)
    except:
        raise(FileNotFoundError)
    
    # drop duplicates for the same person with multiple records
    rec = rec[0:1]
    # convert the single-record dataframe to a tuple (index, dict),
    # in which only dict obj is returned.
    idx , member = rec.to_dict('index').popitem()
    return idx, member

# Functional testing
if __name__ == '__main__':
    path_dir = 'data'  # relative to the current dir
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
        
    # try:
    #     send_email(email_receiver,
    #         subject="Test1",
    #         )
    #     print(f'No body email sent to {email_receiver} ok\n')
        
    #     send_email(email_receiver,
    #         subject="Test2",
    #         f_text=email_text,
    #         )
    #     print(f'Text email sent to {email_receiver} ok\n')

    #     send_email(email_receiver,
    #         subject="Test3",
    #         f_text=email_text,
    #         f_html=email_html,
    #         )
    #     print(f'Text & HTML email sent to {email_receiver} ok\n')

    #     send_email(email_receiver,
    #         subject="Test4",
    #         f_text=email_text,
    #         f_html=email_html,
    #         f_attached=email_attached 
    #         )
    #     print(f'Text & HTML Email with attachment sent to {email_receiver} ok\n')

    # except Exception as err:
    #     print(f"Caught '{err}'. class is {type(err)}")
    #     print(f'send_email(): failed\n')
