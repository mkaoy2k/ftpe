# FamilyTrees Personal Edition (PE) App

## Introduction

---

The 'FamilyTrees' PE App is a stand-alone Python application that allows you to record you family tree.

## How It Works

---

The 'Family Trees' service facilitates you to build your whole family tree as you grow your family, you will be able to add, update or share family info among your family as you like.

The 'Family Trees' service also provides various query functions to trace your root, including to show you graphic representation of your immediate family members. And as you like, download graphs to share via email.

The 'Family Trees' service not only helps you to build your whole family tree, but also provides you with the following benefits:

1. _Sharing_: 
   
   To share with your family tree, simply passing along your credential to them. They can help you to review and build the same family tree of yours. Or better yet, with divide-and-conquer approach, several registered users are allowed to build different parts of the family tree simultaneously. And merge them together later for sharing the whole family tree which might eventually become the legacy of your family heritage.
   
2. _Multi-Language Support_: 
   
   Currently, supported languages: TW, and US

## Dependencies and Installation

---

To install the 'Family Trees' PE App, please follow these steps:

1. Clone the repository to your local machine.

2. Install the required dependencies by running the following command if using Conda environment:

   ```
   conda env create -f environemnt.yaml
   
3. Or under Python environment, run:
   
   python -m pip install -r requirements.txt
   ```

3. Configuration defined in the `.env` file.

```commandline

# Gmail service
EMAIL_PW=your_gmail_pw
EMAIL_SENDER=your_gmail

# Server Logging: 
# LOGGING="DEBUG"

# Turn off logging:
LOGGING="INFO"

# Languages currently supported
L10N = "繁中"
# L10N = "US"
```

## How to Use

---

To use the 'Family Trees' PE App, follow these steps:

1. Ensure that you have installed the required dependencies and added the OpenAI API key to the `.env` file.

2. Run the `family_pe.py` file using the Streamlit CLI. Execute the following command:

   ```
   streamlit run family_pe.py
   ```

3. The application will launch in your default web browser, displaying the main page.

### FAQ

1. _Where is the my FamilyTree stored?_

   The data is stored in a CSV file format, called me.csv, located in the sub-directory, call 'data'.
   
2. _Who created 'FamilyTrees PE'?_
    
   Created with ❤️ by 
   [Michael Kao](https://github.com/mkaoy2k)
