# Eve Pos Taxer

A tool which monitors corporations for POSes in whitelisted systems as well as their tax payment to a defined character.

The result is an overview of which corporations have how much credit or debit.

The balance is calculated of the corporation's deposit minus there amount of used posdays multiplied by a tax of 2.000.000 each. A posday is one pos which is online at one day (at the time of monitoring).

## Prerequisites

* MongoDB (3.2.6 or newer)
* Docker (1.12.3 or newer)
* DockerCompose (1.8.1 or newer)

### Optional

Python 3.5.2 with `pymongo` and `requests` if you want to run the scripts outside of Docker.

### Environment variables

* `EVE_POS_DB_NAME`: Database name, e.g. test.
* `EVE_POS_DB_PORT`: Database port, e.g. 27017.
* `EVE_POS_DB_URL`: Database url (must not include port or database), e.g. localhost.
* `EVE_POS_DB_USERNAME`: Database access user (must have read and write access).
* `EVE_POS_DB_PASSWORD`: Database access password.
* `EVE_POS_AUTHKEY`: A string to authorize API requests (see `app.py#app(...)`).
* `EVE_POS_TAX_RECIPIENT`: The character's name, to whom the corps pay their taxes. This variable is only needed for the script `loadTransactions.py`.

Those variables must all be set in `variables.env` for running the both the scripts image and the API image.

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

1. `docker build . -t eve-pos-taxer` to build the api docker image.
2. `docker build -f Dockerfile_scripts . -t eve-pos-taxer` to build the scripts docker image which depends on the api image.
3. `docker run -it --env-file variables.env eve-pos-loader` to run all of the scripts below.
    1. `loadPos.py` to track all poses which are online. Must be executed every day.
    2. `loadTransactions.py` to track all transactions to the tax recipient. Must be executed to avoid overlooking old transactions.
    3. `buildDepositJournal.py` to calculate the total deposit of all corporations until today. Will drop and recreate the collection.
    4. `buildPosDayJournal.py` to calculate the total posdays of all corporations until today. Will only use systems which are in the collection `location_whitelist`. Will drop and recreate the collection.
    5. `buildBalanceJournal.py` to calculate the current balance of all corporations. Will drop and recreate the collection.
4. `docker-compose up` to serve the REST API at the port set in `docker-compose.yml` (default: 9000).

## API Access

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