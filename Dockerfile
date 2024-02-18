# Dockerfile, Image, Container

FROM umihico/aws-lambda-selenium-python:latest

RUN pip install pipenv

ENV PROJECT_DIR /usr/local/src/code

WORKDIR ${PROJECT_DIR}

COPY ./giftcardsdocker/Pipfile ./giftcardsdocker/Pipfile.lock ${PROJECT_DIR}/

RUN pip install --upgrade cython
RUN pip install --upgrade pip

RUN pipenv install --system --deploy

#COPY ../utils ${PROJECT_DIR}/utils/
#COPY ./lambda_function ${PROJECT_DIR}/lambda_function/
#
## Getting access denied in aws as not same user as locally
#RUN chmod -R 777 .

COPY Automated-Scripts/common/google_photos_upload.py ${LAMBDA_TASK_ROOT}/common/
COPY Automated-Scripts/common/captcha_bypass.py ${LAMBDA_TASK_ROOT}/common/
COPY Automated-Scripts/common/notification_manager.py ${LAMBDA_TASK_ROOT}/common/
COPY Automated-Scripts/common/driver_manager.py ${LAMBDA_TASK_ROOT}/common/
COPY Automated-Scripts/common/email_client.py ${LAMBDA_TASK_ROOT}/common/
COPY Automated-Scripts/common/google_apis.py ${LAMBDA_TASK_ROOT}/common/
COPY Automated-Scripts/common/photoslibrary_creds.json ${LAMBDA_TASK_ROOT}/common/
COPY Automated-Scripts/common/.env ${LAMBDA_TASK_ROOT}/common/

#COPY Automated-Scripts/common/* ${LAMBDA_TASK_ROOT}/common/

COPY ./giftcardsdocker/asda_giftcard_checker_api.py ${LAMBDA_TASK_ROOT}/asda_giftcard_checker_api.py
COPY ./giftcardsdocker/lambda_docker_selenium.py ${LAMBDA_TASK_ROOT}/lambda_docker_selenium.py
COPY ./giftcardsdocker/.env ${LAMBDA_TASK_ROOT}/.env
COPY ./giftcardsdocker/photoslibrary_creds.json ${LAMBDA_TASK_ROOT}/photoslibrary_creds.json

# setting the CMD to your handler file_name.function_name
CMD [ "asda_giftcard_checker_api.handler" ]
#CMD [ "lambda_handler.handler" ]

