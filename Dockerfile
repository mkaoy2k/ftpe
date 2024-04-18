FROM python:3.11.4

WORKDIR /ftpe

COPY . .

RUN python -m pip install -r requirements.txt

CMD [ "streamlit", "run", "./family_pe.py" ]