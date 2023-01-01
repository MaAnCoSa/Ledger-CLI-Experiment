import typer
from datetime import datetime
from tabulate import tabulate
from types import SimpleNamespace

app = typer.Typer()

# This callback functions makes it possible for common options (or common flags) to be available.
@app.callback()
def main(
    ctx: typer.Context,
    sort: str = typer.Option("--sort", "-s", help=" Sorts results by desigantion."),
    file: str = typer.Option("--file", "-f", help=" Designate the journal file path."),
    b: str = typer.Option("--begin", "-b", help=" [YYYY-MM-DD] Filters to only entries after the given date."),
    e: str = typer.Option("--end", "-e", help=" [YYYY-MM-DD] Filters to only entries after the given date."),
    price_db: str = typer.Option("--price-db", help=" Converts commodities by prices in designated file.")
    ):

    ctx.obj = SimpleNamespace(sort = sort, file = file, price_db = price_db, b = b, e = e)


# This functions will read the journal file and save the data in a list of dictionaries whenever
# a command begins.
# -----------------------------------------------------------------------------------------------------------------
lines = []
lines_db = []
journal = []
commodities = []

hom_cur = '$'

def get_amt(ln):
    if ln[0].isdigit():
        amt = ln[0]
        ln.pop(0)
        while ln[0] == '':
            ln.pop(0)
        unit = ln[0]
    else:
        li = [*ln[0]]
        if li[0].isdigit():
            amt = ''
            while li[0].isdigit() or li[0] == '.':
                amt += li[0]
                li.pop(0)
            unit = ''.join(li)
        else:
            unit = ''
            while not li[0].isdigit():
                unit += li[0]
                li.pop(0)
                if len(li) == 0:
                    ln.pop(0)
                    while ln[0] == '':
                        ln.pop(0)
                    amt = ln[0]
                    return [unit, float(amt)]
            amt = ''.join(li)

    return [unit, float(amt)]


def get_data(ctx):
    # Unless a specific file is declared, it will read a default path.
    if ctx.obj.file != "--file":
        file = open(ctx.obj.file, "r")
    else:
        file = open("journal.dat", "r")


    # If the price_db tag was called, this opens the file with the commodities' prices.
    if ctx.obj.price_db != "--price-db":
        db_file = open(ctx.obj.price_db, "r")

        global hom_cur

        ind = -1
        for i in db_file:
            ind += 1
            lines_db.append(i.replace("\n", ""))
            ln = lines_db[ind].split(" ")

            # Tag to declare main currency (or home currency).
            if ln[0] == 'N':
                while ln[0] == "":
                    ln.pop(0)
                hom_cur = ln[0]

            # Tag to declare a commodity and its price.
            if ln[0] == 'P':
                ln.pop(0)
                while ln[0] == "":
                    ln.pop(0)
                date = datetime.strptime(ln[0], '%Y/%m/%d').date()
                dt = date.strftime('%Y-%b-%d')

                ln.pop(0)
                while ln[0] == "":
                    ln.pop(0)
                time = datetime.strptime(ln[0], '%H:%M:%S').time()
                tm = time.strftime('%H:%M:%S')

                ln.pop(0)
                while ln[0] == "":
                    ln.pop(0)
                com = ln[0]

                ln.pop(0)
                while ln[0] == "":
                    ln.pop(0)
                price = ln[0].replace(",", "")
                val = price.split(" ")
                if len(val) == 1:
                    aux = list(val[0])
                    unit = aux.pop(0)
                    price = "".join(aux)
                elif val[0] == '$':
                    unit = val[0]
                    val.pop(0)
                    while val[0] == '':
                        val.pop(0)
                    price = val[0]
                else:
                    price = val[0]
                    val.pop(0)
                    while val[0] == '':
                        val.pop(0)
                    unit = val[0]

                commodities.append({"date": dt+" "+tm, "commodities": [com, unit], "price": [1, float(price)]})
    
        commodities.sort(key=lambda dir : dir["date"])
    

    ind = -1
    for i in file:
        ind += 1
        lines.append(i.replace("\n", "").replace(",", '').replace("\t", "    "))
        ln = lines[ind].split(' ')


        # If an line is a comment, we ignore it.
        if len(ln) == 1: pass
        elif ln[0] == ';': pass
        elif ln[0] == '=': pass
    
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

                if ctx.obj.price_db != "--price-db" and len(commodities) != 0:
                    for x in range(len(commodities)):
                        if unit == commodities[x]["commodities"][0]:
                            unit = commodities[x]["commodities"][1]
                            amt = (amt * commodities[x]["price"][0]) / commodities[x]["price"][1]

                journal[len(journal)-1]["transactions"].append({"ind": ind,
                                                                "account": act.strip(),
                                                                "unit": unit,
                                                                "amount": amt})
            else:
                units = []
                n = len(journal[len(journal)-1]["transactions"])

                for j in range(n):
                    ban = 0
                    if len(units) != 0:
                        for x in range(len(units)):
                            if units[x] != journal[len(journal)-1]["transactions"][j]["unit"]:
                                ban += 1
                    if ban == len(units) or len(units) == 0:
                            units.append(journal[len(journal)-1]["transactions"][j]["unit"])

                for x in range(len(units)):
                    amt = 0
                    for j in range(n):
                        if journal[len(journal)-1]["transactions"][j]["unit"] == units[x]:
                            amt += (journal[len(journal)-1]["transactions"][j]["amount"] * (-1))
                    
                    journal[len(journal)-1]["transactions"].append({"ind": ind,
                                                                    "account": act.strip(),
                                                                    "unit": units[x],
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
    
    if 'd' in ctx.obj.sort:
        journal.sort(key=lambda dir : dir["date"])
    


# -----------------------------------------------------------------------------------------------------------------
# REG command - to display a table of all transactions.

@app.command("reg", help=" [\"keyword keyword ...\"] Displays registers from the journal.")
def register(ctx: typer.Context, filters: str = typer.Argument("all")):
    get_data(ctx)

    b_date = datetime.strptime("1000-01-01", '%Y-%m-%d').date()
    e_date = datetime.strptime("9999-12-31", '%Y-%m-%d').date()

    if ctx.obj.b != '--begin':
        b_date = datetime.strptime(ctx.obj.b, '%Y-%m-%d').date()

    if ctx.obj.e != '--end':
        e_date = datetime.strptime(ctx.obj.e, '%Y-%m-%d').date()


    flts = filters.split(" ")

    table = []
    total = []
    for i in range(len(journal)):

        date = datetime.strptime(journal[i]["date"], '%Y-%b-%d').date()

        if date < b_date or date > e_date:
            continue

        if 'a' in ctx.obj.sort:
            journal[i]["transactions"].sort(key=lambda dir : dir["amount"])
        
        n = len(journal[i]["transactions"])
        ban = 0
        for j in range(n):

            ban1 = 0
            for x in flts:
                if not ((x in journal[i]["concept"]) or (x in journal[i]["transactions"][j]["account"] or x == 'all')):
                    ban1 += 1

            if ban1 == len(flts):
                continue

            ban = 0
            if len(total) != 0:
                for x in range(len(total)):
                    if total[x][0] == journal[i]["transactions"][j]["unit"]:
                        total[x][1] += journal[i]["transactions"][j]["amount"]
                        cur_tot = x
                    else:
                        ban += 1
            if len(total) == 0 or ban == len(total):
                total.append([journal[i]["transactions"][j]["unit"],
                                journal[i]["transactions"][j]["amount"]])
                cur_tot = len(total)-1

            if j == 0:
                table.append([journal[i]["date"],
                            journal[i]["concept"],
                            journal[i]["transactions"][j]["account"],
                            journal[i]["transactions"][j]["unit"],
                            journal[i]["transactions"][j]["amount"],
                            journal[i]["transactions"][j]["unit"],
                            total[cur_tot][1]])
            else:
                table.append(['',
                            '',
                            journal[i]["transactions"][j]["account"],
                            journal[i]["transactions"][j]["unit"],
                            journal[i]["transactions"][j]["amount"],
                            journal[i]["transactions"][j]["unit"],
                            total[cur_tot][1]])


    print("")
    print(tabulate(table))
    print("")


# -----------------------------------------------------------------------------------------------------------------
# BAL command - to display a list of all accounts and their balances.

# This function creates a directory with all balances.
def set_act(accounts, ls, i, j):
    ban = 0
    ban2 = 0
    cur_act = 0

    if len(accounts) != 0:
        for k in range(len(accounts)):
            if ls[0] == accounts[k]["account"]:
                for x in range(len(accounts[k]["amounts"])):
                    if journal[i]["transactions"][j]["unit"] == accounts[k]["amounts"][x]["unit"]:
                        accounts[k]["amounts"][x]["amount"] += journal[i]["transactions"][j]["amount"]
                        cur_act = k
                    
                    else:
                        ban2 += 1

                if ban2 == len(accounts[k]["amounts"]):
                    accounts[k]["amounts"].append({"unit": journal[i]["transactions"][j]["unit"],
                                                    "amount": journal[i]["transactions"][j]["amount"]})
                    cur_act = k
            else:
                ban += 1
    if ban == len(accounts) or len(accounts) == 0:
        accounts.append({"account": ls[0],
                        "amounts": [{"unit": journal[i]["transactions"][j]["unit"],
                                    "amount": journal[i]["transactions"][j]["amount"]}],
                        "subact": []})
        cur_act = len(accounts) - 1

    if len(ls) > 1:
        ls.pop(0)
        set_act(accounts[cur_act]["subact"], ls, i, j)



def check_print(accounts, flts):
    for i in range(len(accounts)):
        ban1 = 0
        for x in flts:
            if not (x in accounts[i]["account"]) and not (x == 'all'):
                ban1 += 1
        if ban1 != len(flts):
            return True
        
    if len(accounts[i]["subact"]) != 0:
        return check_print(accounts[i]["subact"], flts)
    
    return False


# This function iterates over the directory created and prints each balance in the correct format.
def print_act(accounts, flts):
    for i in range(len(accounts)):
        check = check_print([accounts[i]], flts)

        if not check:
            continue

        print_loop([accounts[i]], 0)


def print_loop(accounts, step):
    sp = "  "
    for j in range(step):
            sp += "  "

    for i in range(len(accounts)):
        for j in range(len(accounts[i]["amounts"])):
            unit = accounts[i]["amounts"][j]["unit"]
            amt = accounts[i]["amounts"][j]["amount"]
            if j == len(accounts[i]["amounts"]) - 1:
                act = sp + accounts[i]["account"]
                print("{:>20.2f} {:<5}{:<10}".format(amt, unit, act))
            else:
                print("{:>20.2f} {:<5}".format(amt, unit))

        if len(accounts[i]["subact"]) > 0:
            print_loop(accounts[i]["subact"], step+1)

# This is the Balance functino itself.
@app.command("bal", help=" [\"keyword keyword ...\"] Displays the balance for each account and its subaccounts.")
def balance(ctx: typer.Context, filters: str = typer.Argument("all")):
    get_data(ctx)

    flts = filters.split(" ")

    accounts = []
    for i in range(len(journal)):
        n = len(journal[i]["transactions"])
        for j in range(n):
            ls = journal[i]["transactions"][j]["account"].split(":")
            set_act(accounts, ls, i, j)
    
    
    if 'a' in ctx.obj.sort:
        accounts.sort(key=lambda dir : dir["amounts"][0]["amount"])

    total = []
    for i in range(len(accounts)):
        ban1 = 0
        for x in flts:
            if not (x in accounts[i]["account"] or x == 'all'):
                ban1 += 1
        if ban1 == len(flts):
            continue

        for j in range(len(accounts[i]["amounts"])):
            if len(total) != 0:
                ban = 0
                for k in range(len(total)):
                    if total[k][0] == accounts[i]["amounts"][j]["unit"]:
                        total[k][1] += accounts[i]["amounts"][j]["amount"]
                    elif k == len(total)-1:
                        ban += 1
            if len(total) == 0 or ban == len(total):
                total.append([accounts[i]["amounts"][j]["unit"],
                                accounts[i]["amounts"][j]["amount"]])

    print("")
    print_act(accounts, flts)
    print("   -----------------------")

    for i in range(len(total)):
        print("{:>20.2f} {:<5}".format(total[i][1], total[i][0]))
    print("")


# -----------------------------------------------------------------------------------------------------------------
# PRINT command - to display all journal entries.

@app.command("print", help=" [\"keyword keyword ...\"] Prints out entries from the journal.")
def prnt(ctx: typer.Context, filters: str = typer.Argument("all")):
    get_data(ctx)

    b_date = datetime.strptime("1000-01-01", '%Y-%m-%d').date()
    e_date = datetime.strptime("9999-12-31", '%Y-%m-%d').date()

    if ctx.obj.b != '--begin':
        b_date = datetime.strptime(ctx.obj.b, '%Y-%m-%d').date()

    if ctx.obj.e != '--end':
        e_date = datetime.strptime(ctx.obj.e, '%Y-%m-%d').date()

    flts = filters.split(" ")

    print("")
    for i in range(len(journal)):

        date = datetime.strptime(journal[i]["date"], '%Y-%b-%d').date()

        if date < b_date or date > e_date:
            continue

        ban1 = 0
        cpt_flt = 0
        for x in flts:
            if not (x in journal[i]["concept"] or x == 'all'):
                ban1 += 1

        if ban1 == len(flts):
            for j in range(len(journal[i]["transactions"])):
                for x in flts:
                    if not (x in journal[i]["transactions"][j]["account"] or x == 'all'):
                        ban1 += 1

            if ban1 == (len(flts)*(len(journal[i]["transactions"])+1)):
                continue
            else:
                print(lines[journal[i]["ind"]])
                for j in journal[i]["transactions"]:
                    for x in flts:
                        if (x in j["account"] or x == 'all'):
                            print(lines[j["ind"]])
                print("")
        else:
            print(lines[journal[i]["ind"]])
            for j in journal[i]["transactions"]:
                print(lines[j["ind"]])
            print("")


if __name__ == '__main__':
    app()
