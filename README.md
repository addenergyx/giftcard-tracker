# Giftcard Management
Containerised lambdas for tracking and storing ASDA giftcards

## Intent
I built this workflow because I found no good way to keep track of each card's balance. 
Initialing I'd keep track by checking the balance via the site and add it to my Apple notes. 
This was tiresome when tracking multiple gift cards. 
It shows the current balance and the card number as an iOS push notification.

## Other domain information
In light of the significant value of unused gift cards in the US, this script aims to manage and maximize the usage of gift cards, particularly ASDA gift cards, obtained through an employee perks and discount program.

- The estimated value of unused gift cards in the US was $3 billion at the end of 2019 (Source: Investopedia)
- According to Bankrate, 51% of U.S. adults have unused gift cards, vouchers, or store credits.
- Finder.com reported that Americans have an average of $116 in unused gift cards.

The primary goal of this script is to efficiently track ASDA gift cards obtained through my employer's employee perks program. 
By doing so, it ensures these gift cards are utilised effectively and prevents them from going unused.

## ETL Pipeline
**Extract**: Extracts gift card card number and PIN from links in emails.

**Transform**: Use these extracted details to query a gift card API to get the current balance. Even though the transformation in this case is relatively straightforward (querying an API with existing data), it's still a form of data enrichment and transformation as it's augmenting the original data with additional, valuable information.

**Load**: Finally, it loads this combined data (card details and balance) into a DynamoDB table.

## Architecture Diagram

![Architecture Diagram](./readme-assets/aws_architecture.png)

### Why Dynamodb over RDS?
Given the requirements of this project, DynamoDB seems to be a more suitable choice than RDS. 
DynamoDB's ability to handle unstructured data and its seamless integration with AWS Lambda and S3 make it ideal for this application. 
Its scalability and performance are beneficial for handling the variable load and data structure of gift card information. 
Additionally, the use of DynamoDB aligns well with the serverless architecture of AWS Lambda, providing a more streamlined and efficient solution for this specific use case. 
DynamoDB is managed by AWS, reducing the overhead of database maintenance and management. If this application heavily relied on complex queries, transactions, or relational data operations, RDS may have been a better fit. 

### Why lambda over EC2/Fargate?
- **Event-Driven Architecture**: Lambda functions are ideal for event-driven applications. In this project, functions are triggered by specific events (like the arrival of an email in an S3 bucket).
- **Scalability**: Lambda automatically scales based on the number of incoming requests, which can be beneficial for handling fluctuating workloads without manual intervention.
- **Cost-Effectiveness**: Lambda charges are based on the actual usage (compute time and number of requests), which can be more cost effective for applications with variable or sporadic traffic.

### All giftcards lambda v2
Using SQS and lambda to deal with long running tasks in lambda.
When there are over 10 giftcards the lambda would time out. To avoid this I'm using SQS to queue the giftcards and process them in batches of 5.
As the order of balance checking isn't critical and the primary goal is to achieve higher throughput, a standard queue is used.
![All giftcards lambda v2](readme-assets/all-giftcards-lambda-v2.png)

## Design

The script functions as follows:

- **Email Integration**: Upon the purchase of a gift card, the corresponding email is automatically forwarded to an S3 bucket via SES.
- **Automated Trigger**: The arrival of an email in the S3 bucket triggers an AWS Lambda function.
- **Lambda Function**: The lambda function executes the following tasks:
  - It interacts with the ASDA Giftcards balance API to check the balance of the received gift card.
  - It saves the gift card information to my Google Photos and Dynamodb for easy and convenient access.
  - Executes the `pushover` API to send a notification of the gift card number and balance to my phone.

As I have a few projects that use similar code I created this package for them: [commons-shared-library](https://github.com/addenergyx/common-shared-library)

![screenshots](readme-assets/phone-screenshots.png)

## Response
```
{
    "statusCode": 200,
    "body": {
        "message": "Gift card lambda invoke successful",
        "Balance": 6.48,
        "Added": [],
        "Deleted": [
            "giftcard_6314380605502977.png",
            "giftcard_6314380606090142.png",
            "giftcard_6314380605304854.png",
            "giftcard_6314380654077532.png",
            "giftcard_6314380656222310.png"
        ]
    }
}
```
