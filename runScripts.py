from scripts import loadPos
from scripts import loadTransactions
from scripts import buildPosDayJournal
from scripts import buildDepositJournal


def main():
    loadPos.main()
    loadTransactions.main()
    buildPosDayJournal.main()
    buildDepositJournal.main()

if __name__ == "__main__":
    main()
