# DEPRECATED

The tooling does not fulfill its task anymore, as the game mechanics have changed. As the XML APIs will be shut down in 2018, the tool will eventually fully break.

# Eve Pos Taxer

[ ![Codeship Status for bahrmichael/eve-pos-taxer](https://codeship.com/projects/0b42a360-b955-0134-447f-7a5b9e1f9d50/status?branch=master)](https://codeship.com/projects/194949)
[![Coverage Status](https://coveralls.io/repos/github/bahrmichael/eve-pos-taxer/badge.svg?branch=master)](https://coveralls.io/github/bahrmichael/eve-pos-taxer?branch=master)

A tool which monitors corporations for POSes in whitelisted systems as well as their tax payment to a defined character.

The result is an overview of which corporations have how much credit or debit.

The balance is calculated of the corporation's deposit minus there amount of used posdays multiplied by a tax of 2.000.000 each. A posday is one pos which is online at one day (at the time of monitoring).

## Prerequisites

* MongoDB (3.2.6 or newer)
* Docker (1.12.3 or newer)
* DockerCompose (1.8.1 or newer)
* A fully setup AWS Lambda account with IAM
* Virtualenv
* Python 2.7 and Pip with zappa

### Environment variables

* `EVE_POS_DB_NAME`: Database name, e.g. test.
* `EVE_POS_DB_PORT`: Database port, e.g. 27017.
* `EVE_POS_DB_URL`: Database url (must not include port or database), e.g. localhost.
* `EVE_POS_DB_USERNAME`: Database access user (must have read and write access).
* `EVE_POS_DB_PASSWORD`: Database access password.
* `EVE_POS_AUTHKEY`: A string to authorize API requests (see `app.py#app(...)`).
* `EVE_POS_TAX_RECIPIENT`: The character's name, to whom the corps pay their taxes. This variable is only needed for the script `loadTransactions.py`.
* `EVE_POS_SNS_QUEUE`: ARN of the topic for intra function communication.
* `EVE_POS_SNS_ERROR`: ARN of the topic for error message to be handled by the Error Webhook function.
* `DISCORD_WEBHOOK`: Webhook for Discord.
* `DISCORD_NOTIFIEES`: Space separated list of UserIDs to be notified by the Error Webhook function.

### Database preparation

The app requires the two collections `corporations` and `location_whitelist` to be filled. POSes which are not in  a system listed in `location_whitelist` will be tracked as well, but not included in the balance calculation.

Each entry in `corporations` consists of the following JSON:

```
{
    "corpId" : 12345678,
    "corpName" : "MYCORPORATION",
    "key" : 1234567,
    "vCode" : "zusadf8bbBFAJFHASFHgfkashfG978fas"
}
```

* `corpId` contains the EvE ID of the corporation
* `corpName` contains the name of the corporation to be displayed in the output, may be a nickname
* `key` contains the key code for the EvE XML API. The API must provide access to WalletJournal and StarbaseList (access mask: 1572864).
* `vCode` contains the verification code for the EvE XML API. The API must provide access to WalletJournal and StarbaseList (access mask: 1572864).

Each entry in `location_whitelist` consists of the following JSON:

```
{
    "systemId" : 30002029
}
```

* `systemId` contains the EvE ID of the solar system.

## Run

### API Service

1. `docker build . -t eve-pos-taxer` to build the api docker image.
2. `docker-compose up` to serve the REST API at the port set in `docker-compose.yml` (default: 9000).

### AWS Functions

1. Create a trigger `cron(45 * * * ? *)` to schedule the parser functions every hour at minute 45 (to avoid the daily downtime).
2. Create two SNS topics for and intra function communication and error reporting. The names will later be used for the environment variables `EVE_POS_SNS_QUEUE` and `EVE_POS_SNS_ERROR`. 
3. Update the `functions/**/zappa_settings.json` files with your topic names and the IAM user you use for uploading the functions.
4. Add `sns:publish` and `sns:subscribe` to the lambda execution role, that you use to execute the functions (default: ZappaLambdaExecution).
5. In each function directory, create a virtual environment with `virtualenv env`, activate it with `source env/bin/activate`, install the requirements with `pip install -r requirements.txt` and deploy it to production (if you want that already) with `zappa deploy production`.
6. Open up the trigger from step 1 and connect it with the functions `transactionParser` and `posParser`.
7. Make sure that the builder functions are subscribed to the `EVE_POS_SNS_QUEUE`.
8. Subscribe to `EVE_POS_SNS_ERROR` with either your e-mail or with the discord webhook below.
9. Make sure that every function fulfills the requirements of its README.

#### Function Webhook

* `posParser` to track all poses which are online. Must be executed every day.
* `balanceJournalBuilder` to calculate the current balance of all corporations. Will drop and recreate the collection.
* `transactionParser` to track all transactions to the tax recipient. Must be executed daily to avoid overlooking old transactions. API walking is not yet implemented.
* `depositJournalBuilder` to calculate the total deposit of all corporations until today. Will drop and recreate the collection.
* `posDayJournalBuilder` to calculate the total posdays of all corporations until today. Will only use systems which are in the collection `location_whitelist`. Will drop and recreate the collection.

### Discord Webhook

1. Create a webhook in Discord.
2. Deploy the Error Webhook function.
3. Add the required environment variables and subscribe the function to the topic `EVE_POS_SNS_ERROR`.

## API Access

*Will be migrated to AWS Lambda or Discord bot* 

Adding the url parameter `csv=true` will provide a csv style response.

Example call: `http://localhost:9000/deposit/all?authkey=secure&csv=true`

```
corpId;amount;corpName
12345678;240000000.0;Some Corp
87654321;420000000.0;Boom Boom

```

### deposit/all

Will list the sum of all taxes that were ever paid until today for each corporation. Does not subtract pos fees.

Example call: `http://localhost:9000/deposit/all?authkey=secure`

Example response:

```
[
    {
        "corpId": 12345678, 
        "amount": 100.0, 
        "corpName": "My Reactions"
    }, 
    { ... }
]
```

### deposit/all/sum

Will list the sum of all taxes that were ever paid until today for all corporations together. Does not subtract pos fees.

Example call: `http://localhost:9000/deposit/all/sum?authkey=secure`

Example response:

```
[
    {
        "totalDeposit": 4132000000.0,
    }
]
```

### poscount/all

Will list the amount of POSes that were deployed on the recent day for each corporation.

Example call: `http://localhost:9000/poscount/all?authkey=secure`

Example response:

```
[
    {
        "date": "2017-01-04", 
        "amount": 2, 
        "corp": "My Corp"
    },
    { ... }
]
```

### poscount/all/sum

Will list the amount of POSes that were deployed on the recent day all corporations.

Example call: `http://localhost:9000/poscount/all/sum?authkey=secure`

Example response:

```
[
    {
        "totalPosCount": 102
    }
]
```

### balance/all

Will list the balance of all taxes minus pos fees for all corporations until today.

Example call: `http://localhost:9000/balance/all?authkey=secure`

```
[
    {
        "corpId": 92345678, 
        "negativeSinceDays": 1,
        "balance": 40, 
        "corpName": "My Other Corp"
    }, 
    { ... }
]
```

### balance/negative

Will list all balances from `balance/all` which are negative.

Example call: `http://localhost:9000/balance/negative?authkey=secure`

```
[
    {
        "corpId": 92345678, 
        "negativeSinceDays": 1,
        "balance": -500, 
        "corpName": "My Other Corp"
    }, 
    { ... }
]
```

### errors

Will show a list of api errors which were caught while parsing.

Example call: `http://localhost:9000/errors?authkey=secure`

```
[
    {
        "script": "loadPos", 
        "corpId": 123456, 
        "message": "Could not access the StarbaseList API", 
        "timestamp": "2017-01-10 10:00:00.000000"
    }, 
    { ... }
]
```

### errors/delete

Will delete all errors from the `errors` endpoint. A blank page with status code `200` will be shown if successful.

Example call: `http://localhost:9000/errors/delete?authkey=secure`
