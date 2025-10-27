FROM python:3.13.2

WORKDIR /fts

COPY . .

RUN python -m pip install -r requirements.txt

CMD [ "streamlit", "run", "./fTrees.py" ]