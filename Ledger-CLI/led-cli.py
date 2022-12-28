import typer
from datetime import datetime
from tabulate import tabulate

app = typer.Typer()

# This section will read the journal file and save the data in a list of dictionaries.
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

file = open("test.dat", "r")
for i in file:
    lines = i.replace("\n", "").replace(",", '')
    ln = lines.split(' ')

    # If an line is a comment, we ignore it.
    if len(ln) == 1:
        pass
    elif ln[0] == ';':
        pass
    
    # If an entry begins with a tab, then it is a transaction to be appended to the last entry in the journal.
    elif ln[0] == '':
        while ln[0] == '':
            ln.pop(0)

        if ln[0] == ';': break

        act = ''
        while ln[0] != '':
            act += ' ' + ln[0]
            ln.pop(0)
            if len(ln) == 0:
                break

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
        
        journal[len(journal)-1]["transactions"].append({"account": act,
                                                        "unit": unit,
                                                        "amount": amt})


    # If a line begin with a date (not a tab), then it we create an entry on the journal object.
    else:
        date = datetime.strptime(ln[0], '%Y/%m/%d').date()
        dt = date.strftime('%Y-%b-%d')
        if ln[1] == '*':
            cpt = lines.split(' * ')[1]
        else:
            ln.pop(0)
            cpt = " ".join(ln)
        journal.append({'date': dt,
                        'concept': cpt,
                        'transactions': []})

# -----------------------------------------------------------------------------------------------------------------

# REG command - to display a table of all transactions.
@app.command("reg")
def reg():
    register()

@app.command("register")
def register():
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

    print(tabulate(table))



@app.command("bal")
def bal():
    balance()

@app.command("balance")
def balance():
    print("Balance command")
    # table = []
    # accounts = []
    # for i in range(len(journal)):
    #     n = len(journal[i]["transactions"])
    #     for j in range(n):
    #         ls = journal[i]["transactions"][j]["account"].split(":")
    #         print(ls)
    #         for k in range(len(ls)):
                

if __name__ == '__main__':
    app()

