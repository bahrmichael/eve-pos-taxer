from scripts import loadPos
from scripts import loadTransactions
from scripts import buildPosDayJournal
from scripts import buildDepositJournal
from scripts import buildBalanceJournal
from scripts.loadPos import PosParser


def main():
    PosParser().main()
    loadTransactions.main()
    buildPosDayJournal.main()
    buildDepositJournal.main()
    buildBalanceJournal.main()


if __name__ == "__main__":
    main()
