FROM python

# create src code directory
RUN mkdir =p /code
WORKDIR /code

COPY requirements.txt /code
COPY main.py /code

RUN pip install -r requirements.txt

# default env vars
ENV RETAINFLAG = 'False'
ENV CLEANSESSIONFLAG = 'True'


ENTRYPOINT ["/bin/bash", "-c", "python -u main.py --broker $BROKERHOST --port $PORT"]
