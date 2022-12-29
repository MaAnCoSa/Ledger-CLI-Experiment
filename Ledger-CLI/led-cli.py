import typer
from datetime import datetime
from tabulate import tabulate

app = typer.Typer()

# This callback functions makes it possible for common options (or common flags) to be available.
@app.callback()
def main(
    ctx: typer.Context,
    sort: str = typer.Option("--sort", "-s", help=" Sorts results by desigantion."),
    file: str = typer.Option("--file", "-f", help=" Designate the journal file path.")
    ):

    ctx.obj = SimpleNamespace(sort = sort, file = file)


# This functions will read the journal file and save the data in a list of dictionaries whenever
# a command begins.
# -----------------------------------------------------------------------------------------------------------------
lines = []
journal = []

def get_amt(ls):
    if len(ls[0]) != 1:
        li = [*ls[0]]
        unit = li[0]
        li.pop(0)
        amt = ''.join(li)
        
        return [unit, float(amt)]
    else:
        unit = ls[0]
        ls.pop(0)
        while ls[0] == '':
            ls.pop(0)
        amt = ls[0]

        return [unit, float(amt)]

def get_data(ctx):
    # Unless a specific file is declared, it will read a default path.
    if ctx.obj.file != "--file":
        file = open(ctx.obj.file, "r")
    else:
        file = open("test.dat", "r")

    #file = open("test.dat", "r")
    #file = open("./ledger-sample-files/Income.ledger", "r")
    ind = -1
    for i in file:
        ind += 1
        lines.append(i.replace("\n", "").replace(",", '').replace("\t", "    "))
        ln = lines[ind].split(' ')


        # If an line is a comment, we ignore it.
        if len(ln) == 1:
            pass
        elif ln[0] == ';':
            pass
    
        # If an entry begins with a tab, then it is a transaction to be appended to the last entry in the journal.
        elif ln[0] == '':
            while ln[0] == '':
                ln.pop(0)

            if ln[0] == ';':
                break

            act = ''
            while ln[0] != '':
                act += ' ' + ln[0]
                ln.pop(0)
                if len(ln) == 0: break

            if len(ln) != 0:
                while ln[0] == '':
                    ln.pop(0)

                ls = get_amt(ln)
                unit = ls[0]
                amt = ls[1]
            else:
                amt = 0
                n = len(journal[len(journal)-1]["transactions"])
                for j in range(n):
                    amt += journal[len(journal)-1]["transactions"][j]["amount"]
                amt *= (-1)
                unit = journal[len(journal)-1]["transactions"][0]["unit"]
        
            journal[len(journal)-1]["transactions"].append({"ind": ind,
                                                            "account": act.strip(),
                                                            "unit": unit,
                                                            "amount": amt})


        # If a line begins with a date (not a tab), then we create an entry on the journal object.
        else:
            date = datetime.strptime(ln[0], '%Y/%m/%d').date()
            dt = date.strftime('%Y-%b-%d')
            if ln[1] == '*':
                cpt = lines[ind].split(' * ')[1]
            else:
                ln.pop(0)
                cpt = " ".join(ln)
            journal.append({'ind': ind,
                            'date': dt,
                            'concept': cpt,
                            'transactions': []})

# -----------------------------------------------------------------------------------------------------------------
# REG command - to display a table of all transactions.

@app.command("reg", help="Displays registers from the journal.")
def register(ctx: typer.Context):
    get_data(ctx)

    table = []
    total = 0.00
    for i in range(len(journal)):
        n = len(journal[i]["transactions"])
        for j in range(n):
            total += journal[i]["transactions"][j]["amount"]
            if j == 0:
                table.append([journal[i]["date"],
                            journal[i]["concept"],
                            journal[i]["transactions"][j]["account"],
                            journal[i]["transactions"][j]["unit"],
                            journal[i]["transactions"][j]["amount"],
                            journal[i]["transactions"][j]["unit"],
                            total])
            else:
                table.append(['',
                            '',
                            journal[i]["transactions"][j]["account"],
                            journal[i]["transactions"][j]["unit"],
                            journal[i]["transactions"][j]["amount"],
                            journal[i]["transactions"][j]["unit"],
                            total])

    print("")
    print(tabulate(table))
    print("")


# -----------------------------------------------------------------------------------------------------------------
# BAL command - to display a list of all accounts and their balances.

# This function creates a directory with all balances.
def set_act(accounts, ls, i, j):
    ban = 0
    cur_act = 0
    if len(accounts) != 0:
        for k in range(len(accounts)):
            if ls[0] == accounts[k]["account"]:
                accounts[k]["amount"] += journal[i]["transactions"][j]["amount"]
                cur_act = k
                break
            elif len(accounts) == (k + 1):
                ban = 1
    if ban == 1 or len(accounts) == 0:
        accounts.append({"account": ls[0], "amount": journal[i]["transactions"][j]["amount"], "subact": []})
        cur_act = len(accounts) - 1

    if len(ls) > 1:
        ls.pop(0)
        set_act(accounts[cur_act]["subact"], ls, i, j)

# This function iterates over the directory created and prints each balance in the correct format.
def print_act(accounts, step):
    sp = "  "
    for j in range(step):
            sp += "  "
    
    for i in range(len(accounts)):
        amt = accounts[i]["amount"]
        act = sp + accounts[i]["account"]
        print("{:>20.2f}{:<10}".format(amt, act))

        if len(accounts[i]["subact"]) > 0:
            print_act(accounts[i]["subact"], step+1)
    
# This is the Balance functino itself.
@app.command("bal", help="Displays the balance for each account and its subaccounts.")
def balance(ctx: typer.Context):
    get_data(ctx)

    accounts = []
    for i in range(len(journal)):
        n = len(journal[i]["transactions"])
        for j in range(n):
            ls = journal[i]["transactions"][j]["account"].split(":")
            set_act(accounts, ls, i, j)

    total = 0.0
    for i in range(len(accounts)):
        total += accounts[i]["amount"]
    step = 0
    print("")
    print_act(accounts, step)
    print("   -----------------")
    print("{:>20.2f}\n".format(total))


# -----------------------------------------------------------------------------------------------------------------
# PRINT command - to display all journal entries.

@app.command("print", help="Prints out entries from the journal.")
def prnt(ctx: typer.Context):
    get_data(ctx)

    #print(ctx.obj.file)

    print("")
    for i in range(len(journal)):
        start = journal[i]["ind"]
        if len(journal) == (i + 1):
            end = len(lines)
        else:
            n = len(journal[i]["transactions"])
            end = journal[i]["transactions"][n-1]["ind"]+1
        for j in range(end-start):
            print(lines[start+j])
        print("")

        
if __name__ == '__main__':
    app()

