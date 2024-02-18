# Giftcard Management
Containerised lambdas for tracking and storing ASDA giftcards

## Intent
In light of the significant value of unused gift cards in the US, this script aims to manage and maximize the usage of gift cards, particularly ASDA gift cards, obtained through an employee perks and discount program.

- The estimated value of unused gift cards in the US was $3 billion at the end of 2019 (Source: Investopedia)
- According to Bankrate, 51% of U.S. adults have unused gift cards, vouchers, or store credits.
- Finder.com reported that Americans have an average of $116 in unused gift cards.

The primary goal of this script is to efficiently track ASDA gift cards obtained through my employer's employee perks program. 
By doing so, it ensures these gift cards are utilized effectively and prevents them from going unused.

## Architecture Diagram

![Architecture Diagram](./readme-assets/aws_architecture.png)

## Design

The script functions as follows:

- **Email Integration**: Upon the purchase of a gift card, the corresponding email is automatically forwarded to an S3 bucket via SES.
- **Automated Trigger**: The arrival of an email in the S3 bucket triggers an AWS Lambda function.
- **Lambda Function**: The lambda function executes the following tasks:
  - It interacts with the ASDA Giftcards balance API to check the balance of the received gift card.
  - It saves the gift card information to my Google Photos and Dynamodb for easy and convenient access.
  - Executes the `pushover` API to send a notification of the gift card number and balance to my phone.

## Response
```
{
    "statusCode": 200,
    "body": {
        "message": "Giftcard lambda invoke successful",
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

![screenshots](readme-assets/phone-screenshots.png)