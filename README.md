# FamilyTrees Personal Edition (`ftpe`)

## Introduction

The 'FamilyTrees' Personal Edition (`ftpe` in short) is a stand-alone web application, wrritten in Python that allows you to record your family tree at your own laptop/PC.

## How It Works

The `ftpe` facilitates you to build your whole family tree as you grow your family and tracing back your family root as long as you like. With this `ftpe` App, you will also be able to add, update, share and pass along your family tree among your family members as unique family heritage.

The `ftpe` also provides various query functions to discover your root, by showing you graphic representation of your immediate family members.

The `ftpe` not only helps you to build your family heritage, but also provides you with the following benefits:

1. _Sharing_:

   To export and import the data file in CSV format of your family tree, you can help  build the same family tree of yours. Or better yet, with divide-and-conquer approach, several family members can work together to build different parts of the family tree simultaneously. And merge them together later for the whole picture of your family tree which might eventually become the treasure of your family heritage.

2. _Multi-Language Support_:

   Currently, there are currently five supported languages: TW, CN, JP, KR and US. You are welcome if you are interested in localizing any language of yours or any comments. Please let [me](mailto:mkaoy2k@gmail.com) know.

## Dependencies and Installation

To install the `ftpe` App in Python environment, follow the following steps:

1. Clone the repository to your local machine.

2. Install the required dependencies by running the following command if using Conda environment:

   ```bash
   conda env create -f environment.yaml
   ```

3. Or under Python environment, run:

   ```bash
   python -m pip install -r requirements.txt
   ```

## Configuration Defined in the `.env` file

Rename 'template.env.txt' to '.env' in your environment and configure the followings:

### Server Logging: 2 options

```bash
LOGGING="DEBUG"
LOGGING="INFO"
```

comment out what you don't want.

### Languages: 5 supported

```bash
L10N = "繁中"
L10N = "US"
L10N = "简中"
L10N = "日本語"
L10N = "한국어"
```

To set the default language, comment out what you don't want.

## How to Use

There are two running environments that are supported to run `ftpe` App.

1. To run `ftpe` App as a Docker Image in a Docker Container:

   - After pulling mkaoy2k/ftpe image from the [Docker Hub](https://hub.docker.com), execute the following command to launch `ftpe` container, for example:

   ```bash
   docker run --name ftpe -d -p 8501:8501 mkaoy2k/ftpe:1.7
   ```

   - At your default web browser, displaying the main page by entering:

   ```bash
   http://localhost:8501
   ```

2. To run `ftpe` App in Python environment, do:

   - Ensure that you have installed the required dependencies in the `.env` file.

   - Run the `family_pe.py` file using the Streamlit CLI. Execute the following command to launch 'ftpe' server:

   ```bash
   streamlit run family_pe.py
   ```

   - When the `ftpe` server is running, your default web browser, displaying the main page, will be launched automatically. Or at will, you may launch your default web browser, displaying the main page by entering:

   ```bash
   http://localhost:8501
   ```

## FAQ

1. _Where is the my FamilyTree stored?_

   The data is stored in a CSV format, called me.csv, located in the sub-directory, call 'data'.

2. _Who created 'FamilyTrees PE'?_

   Created with ❤️ by:
   [Michael Kao](https://github.com/mkaoy2k)
