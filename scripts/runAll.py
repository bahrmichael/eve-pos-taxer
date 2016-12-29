import loadPos
import loadTransactions
import buildPosDayJournal
import buildDepositJournal


def main():
    loadPos.main()
    loadTransactions.main()
    buildPosDayJournal.main()
    buildDepositJournal.main()

if __name__ == "__main__":
    main()
