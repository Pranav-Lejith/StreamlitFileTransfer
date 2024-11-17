import streamlit as st
import os
import base64
import hashlib
import json
import time
import zipfile
import io
import shutil

# Set page config for a wider layout and dark theme
st.set_page_config(layout="wide", page_title="File Sharer", page_icon="🚀")

# Custom CSS for futuristic look
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(45deg, #1e1e1e, #2d2d2d);
        color: #e0e0e0;
    }
    .stButton>button {
        background-color: #00a86b;
        color: white;
        border-radius: 20px;
        border: none;
        padding: 10px 24px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #008f5b;
        transform: scale(1.05);
    }
    .file-info {
        background-color: rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
        transition: all 0.3s ease;
    }
    .file-info:hover {
        background-color: rgba(255,255,255,0.2);
        transform: translateY(-5px);
    }
    .download-button, .delete-button {
        display: inline-block;
        color: white !important;
        text-decoration: none;
        padding: 8px 16px;
        border-radius: 20px;
        transition: all 0.3s ease;
        text-align: center;
        margin: 5px 0;
    }
    .download-button {
        background-color: #00a86b;
    }
    .download-button:hover {
        background-color: #008f5b;
        transform: scale(1.05);
        text-decoration: none;
    }
    .delete-button {
        background-color: #ff4757;
    }
    .delete-button:hover {
        background-color: #ff6b81;
        transform: scale(1.05);
        box-shadow: 0 0 15px #ff4757;
    }
    @keyframes glow {
        0% { box-shadow: 0 0 5px #00a86b; }
        50% { box-shadow: 0 0 20px #00a86b; }
        100% { box-shadow: 0 0 5px #00a86b; }
    }
    .glow-effect {
        animation: glow 2s infinite;
    }
    .command-prompt {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
    }
    .command-prompt-window {
        position: fixed;
        bottom: 80px;
        right: 20px;
        width: 400px;
        background-color: #000000;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 0 20px rgba(255,0,0,0.5);
        z-index: 1000;
    }
    .close-button {
        position: absolute;
        top: 10px;
        right: 10px;
        cursor: pointer;
        color: #ff0000;
    }
</style>
""", unsafe_allow_html=True)

def create_splash_html(text, color):
    return f"""
    <style>
    .typewriter h1 {{
      overflow: hidden;
      color: {color};
      white-space: nowrap;
      margin: 0 auto;
      letter-spacing: .15em;
      border-right: .15em solid orange;
      animation: typing 3.5s steps(30, end), blink-caret .5s step-end infinite;
    }}

    @keyframes typing {{
      from {{ width: 0 }}
      to {{ width: 100% }}
    }}

    @keyframes blink-caret {{
      from, to {{ border-color: transparent }}
      50% {{ border-color: orange }}
    }}
    </style>
    <div class="typewriter">
        <h1>{text}</h1>
    </div>
    """

# Set the upload directory
UPLOAD_DIR = "uploaded_files"
METADATA_FILE = "file_metadata.json"

# Create the upload directory if it doesn't exist
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Load or create metadata
if os.path.exists(METADATA_FILE):
    with open(METADATA_FILE, 'r') as f:
        file_metadata = json.load(f)
else:
    file_metadata = {}

def save_file(uploaded_file, password):
    file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Save metadata
    file_metadata[uploaded_file.name] = {
        'password': hashlib.sha256(password.encode()).hexdigest() if password else None
    }
    with open(METADATA_FILE, 'w') as f:
        json.dump(file_metadata, f)

def get_file_download_link(file_path, filename):
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}" class="download-button glow-effect">Download {filename}</a>'

def delete_file(filename):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        if filename in file_metadata:
            del file_metadata[filename]
            with open(METADATA_FILE, 'w') as f:
                json.dump(file_metadata, f)
        return True
    return False

def save_folder(uploaded_files, folder_name):
    folder_path = os.path.join(UPLOAD_DIR, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    
    for uploaded_file in uploaded_files:
        file_path = os.path.join(folder_path, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

def get_folder_download_link(folder_path, folder_name):
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zf.write(file_path, os.path.relpath(file_path, folder_path))
    memory_file.seek(0)
    b64 = base64.b64encode(memory_file.getvalue()).decode()
    return f'<a href="data:application/zip;base64,{b64}" download="{folder_name}.zip" class="download-button glow-effect">Download {folder_name}</a>'

def download_all_files():
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for root, dirs, files in os.walk(UPLOAD_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                zf.write(file_path, os.path.relpath(file_path, UPLOAD_DIR))
    memory_file.seek(0)
    b64 = base64.b64encode(memory_file.getvalue()).decode()
    st.markdown(f'<a href="data:application/zip;base64,{b64}" download="all_files.zip" class="download-button glow-effect">Download All Files</a>', unsafe_allow_html=True)

# Initialize session state
if 'show_main_content' not in st.session_state:
    st.session_state.show_main_content = False
if 'show_command_prompt' not in st.session_state:
    st.session_state.show_command_prompt = False
if 'is_developer' not in st.session_state:
    st.session_state.is_developer = False
if 'splash_shown' not in st.session_state:
    st.session_state.splash_shown = False

# Splash screen
if not st.session_state.splash_shown:
    splash = st.empty()
    splash.markdown(create_splash_html("File Sharer", '#48CFCB'), unsafe_allow_html=True)
    time.sleep(4)  # Display splash for 4 seconds
    st.session_state.splash_shown = True
    st.session_state.show_main_content = True
    splash.empty()

# Command Prompt
def command_prompt():
    st.markdown("""
    <div class="command-prompt-window">
        <div class="close-button" onclick="document.querySelector('.command-prompt-window').style.display='none';">X</div>
        <h3 style="color: #ff0000;">Command Prompt</h3>
        <div id="command-output" style="color: #ff0000; margin-bottom: 10px;"></div>
        <input type="text" id="command-input" placeholder=">>>" style="width: 100%; background-color: #000000; color: #ff0000; border: 1px solid #ff0000;">
    </div>
    """, unsafe_allow_html=True)

    command = st.text_input("", key="command_input", label_visibility="collapsed")
    
    if command:
        if command in ['override protocol-amphibiar', 'override command-amphibiar', 
                       'command override-amphibiar', 'command override-amphibiar23', 
                       'control override-amphibiar', 'system override-amphibiar', 'user:amphibiar']:
            st.session_state.is_developer = True
            st.markdown(create_splash_html("Welcome Developer", '#FF6B6B'), unsafe_allow_html=True)
            time.sleep(2)
            st.session_state.show_command_prompt = False
            st.rerun()
        elif command.lower() == 'downloadall':
            download_all_files()
            st.success("All files have been prepared for download.")
            st.rerun()
        elif command.lower() == 'exit dev mode':
            st.session_state.is_developer = False
            st.success("Exited developer mode.")
            st.rerun()
        else:
            st.error("Invalid command")

# Main content
if st.session_state.show_main_content:
    # App layout
    st.title("🚀 :red[File Sharer] (:blue[Created By: :red[Amphibiar ]])")

    # File/Folder upload section
    upload_type = st.radio("Upload type", ("File", "Folder"))
    
    if upload_type == "File":
        uploaded_file = st.file_uploader("Choose a file to upload", type=None)
        if uploaded_file is not None:
            st.write(f"Uploaded: {uploaded_file.name}")
            password = st.text_input("Set a password for this file (optional)", type="password")
            if st.button("Upload File", key="upload"):
                save_file(uploaded_file, password)
                st.success("File uploaded successfully!")
                st.balloons()
    else:
        uploaded_files = st.file_uploader("Choose files to upload", type=None, accept_multiple_files=True)
        if uploaded_files:
            folder_name = st.text_input("Enter folder name")
            if st.button("Upload Folder", key="upload_folder"):
                save_folder(uploaded_files, folder_name)
                st.success(f"Folder '{folder_name}' uploaded successfully!")
                st.balloons()

    # Display uploaded files and folders
    st.header("📁 Uploaded Files and Folders")
    uploaded_items = os.listdir(UPLOAD_DIR)

    if uploaded_items:
        for item in uploaded_items:
            item_path = os.path.join(UPLOAD_DIR, item)
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"<div class='file-info'>{'📁' if os.path.isdir(item_path) else '📄'} {item}</div>", unsafe_allow_html=True)
            with col2:
                if os.path.isdir(item_path):
                    st.markdown(get_folder_download_link(item_path, item), unsafe_allow_html=True)
                else:
                    if file_metadata.get(item, {}).get('password'):
                        password_attempt = st.text_input(f"Password for {item}", type="password", key=f"pwd_{item}")
                        if st.button("Download", key=f"btn_{item}"):
                            if hashlib.sha256(password_attempt.encode()).hexdigest() == file_metadata[item]['password']:
                                st.markdown(get_file_download_link(item_path, item), unsafe_allow_html=True)
                            else:
                                st.error("Incorrect password!")
                    else:
                        st.markdown(get_file_download_link(item_path, item), unsafe_allow_html=True)
            with col3:
                if st.session_state.is_developer:
                    if st.button("🗑️ Delete", key=f"del_{item}", help=f"Delete {item}"):
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                        else:
                            delete_file(item)
                        st.success(f"{item} has been deleted.")
                        st.rerun()

    else:
        st.info("No files or folders uploaded yet.")

    # Password information dropdown
    with st.expander("🔐 Password Information"):
        st.write("Files with passwords:")
        for file, metadata in file_metadata.items():
            if metadata.get('password'):
                st.write(f"- {file}")

    # Add a note about file persistence
    st.info("Note: Uploaded files and folders are saved on the server and will be available for all users until the app is restarted or the items are manually deleted.")

    # Command Prompt Button
    st.markdown('<div class="command-prompt">', unsafe_allow_html=True)
    if st.button("Command Prompt"):
        st.session_state.show_command_prompt = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Show Command Prompt if activated
if st.session_state.show_command_prompt:
    command_prompt()