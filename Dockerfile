FROM python:3.13.2

WORKDIR /ftpe

COPY . .

RUN python -m pip install -r requirements.txt

CMD [ "streamlit", "run", "./ftpe_ui.py" ]