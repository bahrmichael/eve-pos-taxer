from scripts import buildBalanceJournal
from scripts import buildDepositJournal
from scripts.buildPosDayJournal import PosDayJournalBuilder
from scripts.loadPos import PosParser
from scripts.loadTransactions import TransactionParser


def main():
    PosParser().main()
    TransactionParser().main()
    PosDayJournalBuilder().main()
    buildDepositJournal.main()
    buildBalanceJournal.main()


if __name__ == "__main__":
    main()
