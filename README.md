# FamilyTrees Personal Edition (`ftpe`)

## Introduction

The 'FamilyTrees' Personal Edition (FamilyTreesPE,`ftpe` in short) is a stand-alone web application, wrritten in Python that allows you to record your family tree at your own laptop/PC.

## How It Works

The `ftpe` facilitates you to build your whole family tree as you grow your family and to be able to trace back your family root as you like. With this simple `ftpe` App, you can add, update, share and pass along your family tree among your family members. Who knows, it might become one of your family heritage some day.

The `ftpe` also provides various query functions to discover your root, by entertaining you with graphic representation of your related family members.

The `ftpe` not only helps you to build your family heritage, but also provides you with the following benefits:

1. _Sharing_:

   To export and import the data file in CSV format of your family tree, you can help  build the same family tree of yours. Or better yet, with divide-and-conquer approach, several family members can work together to build different parts of the family tree simultaneously. And merge them together later for the whole picture of your family tree which might eventually become the treasure of your family heritage.

2. _Multi-Language Support_:

   Currently, there are 10 supported languages: English, Traditional Chinese, Simplified Chinese, Japanese, Korean, Danish, German, French, Lithuanian, and Polish. You are welcome if you would like to localize any language of yours or to provide any comments. Don't hesitate to let [Creator: Michael Kao](mailto:mkaoy2k@gmail.com) know.

### System Requirements

- Python 3.8 or newer
- SQLite 3 (built-in)
- Email service (e.g., Gmail)

### Installation Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/mkaoy2k/subs.git
   cd subs
   ```

2. **Create Virtual Environment (Recommended)**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or
   .\.venv\Scripts\activate  # Windows
   ```

3. **Install Dependencies**

   Install the required dependencies by running the following command if using Conda environment:

   ```bash
   conda env create -f environment.yaml
   ```

   Or under uv environment, run:

   ```bash
   uv run python -m pip install -r requirements.txt
   ```

   Or under pip environment, run:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables** defined in the `.env` file

   ```bash
   cp template.env.txt .env
   ```

   Edit the `.env` file to tailor your environment:
   - Set server paths
   - Set your language, release, and version etc.
   - Configure email service
   - Set application name, DB admin name, DB admin password
   - Set DB name, DB host, DB port
   - Configure server URL

   Edit `L10N.json` if your language is newly added. The default languages are Traditional Chinese (繁中) and English (US).

   Edit `L10N_<your language>.json` if your language is newly added. The current localization files include:

   ```bash
   "繁中"  : "L10N_TW.json",
   "简中"  : "L10N_CN.json",
   "日本語" : "L10N_JP.json",
   "한국어" : "L10N_KR.json",
   "DANISH" : "L10N_DK.json",
   "GERMAN" : "L10N_DE.json",
   "FRENCH" : "L10N_FR.json",
   "LITHUANIAN" : "L10N_LT.json",
   "POLISH" : "L10N_PL.json",
   "US"   : "L10N_US.json"
   ```

   To set your preferred language, you can specify your preferred language in the `.env` file, e.g.:

   ```bash
   L10N_FILE="L10N.json"
   L10N="繁中"
   # L10N="US"
   ```

   At the run time, from `Settings` sidebar, you can also select your preferred language from the 'User Language' drop-down list.

5. **Initialize Data Directory**

   ```bash
   mkdir -p data
   ```

6. **Initialize Admin User Database**

   ```bash
   python genesis.py
   ```

## Directory Structure

ftpe/
├── ftpe_ui.py           # Main interface
├── auth_utils.py         # Authentication utilities
├── context_utils.py      # Context management
├── db_utils.py           # Database utilities
├── email_utils.py        # Email functionality
├── family_pe.py          # Main application
├── funcUtils.py          # Utility functions
├── genesis.py            # Initialization script
├── glogTime.py           # Logging utilities
├── migrate_members.py    # Data migration script
├── ops_dbMgmt.py         # Database management
├── prod_backup.sh        # Production backup script
├── prod_push.sh          # Production deployment script
├── requirements.txt      # Python dependencies
├── template.env.txt      # Environment template
│
├── data/                 # Data directory
│   ├── family.db        # Family database
│   ├── me.csv           # Personal data
│   ├── members_export_*.csv  # Member exports
│   ├── template.csv     # CSV template
│   └── users.json       # User data
│
└── pages/                # Application pages
    ├── 1_usrMgmt.py     # User management
    ├── 2_famMgmt.py     # Family management
    ├── 3_csv_editor.py  # CSV editor
    ├── 4_json_editor.py # JSON editor
    └── 5_ftpe.py        # Main application page

## How to Use

There are two running environments that are supported to run `ftpe` App.

1. To run `ftpe` App as a Docker Image in a Docker Container:

   - After pulling mkaoy2k/ftpe image from the [Docker Hub](https://hub.docker.com), execute the following command to launch `ftpe` container, for example:

   ```bash
   docker run --name ftpe -d -p 8501:8501 mkaoy2k/ftpe:2.6
   ```

   - At your default web browser, displaying the login page by entering:

   ```bash
   http://localhost:8501
   ```

2. To run `ftpe` App in Python environment, do:

   - Ensure that you have installed the required dependencies in the `.env` file.

   - Run the `ftpe_ui.py` file using the Streamlit CLI. Execute the following command to launch `ftpe` server:

   ```bash
   streamlit run ftpe_ui.py
   ```

   - When the `ftpe` server is running, your default web browser, displaying a login page, will be launched automatically. Or at will, you may launch your default web browser, displaying the login page by entering:

   ```bash
   http://localhost:8501
   ```

## FAQ

1. _Where is the my FamilyTree data stored?_

   The data file is stored in a CSV format, called me.csv, located in the sub-directory, call 'data'.

2. _Who created 'ftpe' (FamilyTrees PE)?_

   Created with ❤️ by:
   [Michael Kao](https://github.com/mkaoy2k/ftpe)
