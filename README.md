# Eve Pos Taxer

A tool which monitors corporations for POSes in whitelisted systems as well as their tax payment to a defined character.

The result is an overview of which corporations have how much credit or debit.

The balance is calculated of the corporation's deposit minus there amount of used posdays multiplied by a tax of 2.000.000 each. A posday is one pos which is online at one day (at the time of monitoring).

## Prerequisites

* MongoDB (3.2.6 or newer)
* Docker (1.12.3 or newer)
* DockerCompose (1.8.1 or newer)
* Python 2.7, pymongo, requests (both only needed for the load and build scripts)

### Environment variables

* `EVE_POS_DB_NAME`: Database name, e.g. test.
* `EVE_POS_DB_PORT`: Database port, e.g. 27017.
* `EVE_POS_DB_URL`: Database url (must not include port or database), e.g. localhost.
* `EVE_POS_DB_USERNAME`: Database access user (must have read and write access).
* `EVE_POS_DB_PASSWORD`: Database access password.
* `EVE_POS_AUTHKEY`: A string to authorize API requests (see `app.py#app(...)`).
* `EVE_POS_TAX_RECIPIENT`: The character's name, to whom the corps pay their taxes. This variable is only needed for the script `loadTransactions.py`.

Those variables must be set on the os level for running the scripts, and must be set in `variables.env` for running the API app.

### Database preparation

The app requires the two collections `corporations` and `location_whitelist` to be filled. POSes which are not in  a system listed in `location_whitelist` will be tracked as well, but not included in the balance calculation.

Each entry in `corporations` consists of the following JSON:

```
{
    "corpId" : "12345678",
    "corpName" : "MYCORPORATION",
    "key" : "1234567",
    "vCode" : "zusadf8bbBFAJFHASFHgfkashfG978fas"
}
```

* `corpId` contains the EvE ID of the corporation
* `corpName` contains the name of the corporation to be displayed in the output, may be a nickname
* `key` contains the key code for the EvE XML API.
* `vCode` contains the verification code for the EvE XML API.

Each entry in `location_whitelist` consists of the following JSON:

```
{
    "systemId" : 30002029
}
```

* `systemId` contains the EvE ID of the solar system.

## Run

1. `python loadPos.py` to track all poses which are online. Must be executed every day.
2. `python loadTransactions.py` to track all transactions to the tax recipient. Must be executed to avoid overlooking old transactions.
3. `python buildDepositJournal.py` to calculate the total deposit of all corporations until today. Will drop and recreate the collection.
4. `python buildPosDayJournal.py` to calculate the total posdays of all corporations until today. Will only use systems which are in the collection `location_whitelist`. Will drop and recreate the collection.
5. `docker build . -t eve-pos-taxer` to build the api docker image.
5. `docker-compose up` to serve the REST API at the port set in `docker-compose.yml` (default: 9000).

## API Access

### deposit/all

Will list the sum of all taxes that were ever paid until today. Does not subtract pos fees.

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

### balance/all

Will list the balance of all taxes minus pos fees for all corporations until today.

Example call: `http://localhost:9000/balance/all?authkey=secure`

```
[
    {
        "corpId": "92345678", 
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
        "corpId": "92345678", 
        "balance": -500, 
        "corpName": "My Other Corp"
    }, 
    { ... }
]
```