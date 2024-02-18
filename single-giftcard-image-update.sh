#!/bin/bash

STACK_NAME="containerised-giftcard-lambda-stack"
TEMPLATE_FILE="single-giftcard-template.yaml"
FUNCTION_NAME="containerised-giftcard-lambda"
IMAGE_URI="xxxxxxxx.dkr.ecr.eu-west-1.amazonaws.com/containerised-giftcard-lambda:latest"

pipenv lock
pipenv sync
pipenv run pip freeze > requirements.txt
aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin xxxxxxxx.dkr.ecr.eu-west-1.amazonaws.com

# https://stackoverflow.com/questions/24537340/docker-adding-a-file-from-a-parent-directory
# Unfortunately, (for practical and security reasons I guess), if you want to add/copy local content, it must be located under the same root path than the Dockerfile

# Try to create the CloudFormation stack
aws cloudformation create-stack --stack-name $STACK_NAME --template-body file://$TEMPLATE_FILE --capabilities CAPABILITY_IAM

aws cloudformation wait stack-create-complete --stack-name $STACK_NAME

# Capture the exit status of the CloudFormation create command
CFN_CREATE_EXIT_STATUS=$?

# If the CloudFormation create was successful (exit status 0), then no further action is needed
if [ $CFN_CREATE_EXIT_STATUS -eq 0 ]; then
    echo "CloudFormation stack created successfully."
    cd ../

    docker build -t containerised-giftcard-lambda -f giftcardsdocker/SingleGiftcardDockerfile .

    docker tag containerised-giftcard-lambda:latest xxxxxxxx.dkr.ecr.eu-west-1.amazonaws.com/containerised-giftcard-lambda:latest

    docker push xxxxxxxx.dkr.ecr.eu-west-1.amazonaws.com/containerised-giftcard-lambda:latest

    aws lambda update-function-code --function-name $FUNCTION_NAME --image-uri $IMAGE_URI

else
    echo "CloudFormation stack creation failed, trying to update the stack..."

    # Try to update the CloudFormation stack
    aws cloudformation update-stack --stack-name $STACK_NAME --template-body file://$TEMPLATE_FILE --capabilities CAPABILITY_IAM

    # Capture the exit status of the CloudFormation update command
    CFN_UPDATE_EXIT_STATUS=$?

    # If the CloudFormation update failed (non-zero exit status), then try updating the function code directly
    if [ $CFN_UPDATE_EXIT_STATUS -ne 0 ]; then
        echo "CloudFormation stack update failed, trying to update the Lambda function code directly..."
        aws lambda update-function-code --function-name $FUNCTION_NAME --image-uri $IMAGE_URI

        # Capture the exit status of the Lambda update command
        LAMBDA_UPDATE_EXIT_STATUS=$?

        if [ $LAMBDA_UPDATE_EXIT_STATUS -eq 0 ]; then
            echo "Lambda function code updated successfully."
        else
            echo "Lambda function code update failed, trying to delete and recreate the stack..."

            # Delete the stack
            aws cloudformation delete-stack --stack-name $STACK_NAME

            # Wait for the stack to be deleted
            echo "Waiting for stack to be deleted..."
            aws cloudformation wait stack-delete-complete --stack-name $STACK_NAME

            # Recreate the stack
            echo "Recreating the CloudFormation stack..."
            aws cloudformation create-stack --stack-name $STACK_NAME --template-body file://$TEMPLATE_FILE --capabilities CAPABILITY_IAM

            aws cloudformation wait stack-create-complete --stack-name $STACK_NAME

            # Capture the exit status of the recreation
            CFN_RECREATE_EXIT_STATUS=$?
            if [ $CFN_RECREATE_EXIT_STATUS -eq 0 ]; then
                echo "CloudFormation stack recreated successfully."

                cd ../

                docker build -t containerised-giftcard-lambda -f giftcardsdocker/SingleGiftcardDockerfile .

                docker tag containerised-giftcard-lambda:latest xxxxxxxx.dkr.ecr.eu-west-1.amazonaws.com/containerised-giftcard-lambda:latest

                docker push xxxxxxxx.dkr.ecr.eu-west-1.amazonaws.com/containerised-giftcard-lambda:latest

                aws lambda update-function-code --function-name $FUNCTION_NAME --image-uri $IMAGE_URI
            else
                echo "CloudFormation stack recreation failed."
            fi
        fi
    else
        echo "CloudFormation stack updated successfully."
    fi
fi

