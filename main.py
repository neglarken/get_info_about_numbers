import sqlite3
import requests
import csv
import re
import shutup; shutup.please() #shut up warnings

def getDataFromResponse(number):
    response = requests.get(f'https://opendata.digital.gov.ru/api/v1/abcdef/phone?num={number}&limit=10', verify=False)
    if response.status_code == 200:
        resJson = response.json()
        if len(resJson['data']) == 0:
            print(f'no data found for number {number}')
            return False
        if resJson['meta']['total'] > resJson['meta']['limit']:
            total = resJson['meta']['total']
            response = requests.get(f'https://opendata.digital.gov.ru/api/v1/abcdef/phone?num={number}&limit={total}', verify=False)
        return response.json()['data']
    else:
        return False

def addPhoneToDB(con, number, data, oid):
    for i in data:
        values = (oid, number, i['code'], f"{i['begin']}-{i['end']}", i['operator'], i['region'])
        try:
            con.execute('insert into phone_info (oid, number, cod, diapazon, operator, region) values (?, ?, ?, ?, ?, ?)', values)
            return True
        except Exception as e:
            print('error inserting number to database', e)
            return False

def validatePhoneNumber(number):
    try:
        return number[-10:]
    except Exception as e:
        return False

def getInfoAboutPhoneNumbersToCSV():
    try:
        print("connecting to database...")
        con = sqlite3.connect('test.db')
        con.execute("create table if not exists phone_info (id integer primary key autoincrement, oid integer, number text, data date default current_date, cod text, diapazon text, operator text, region text)")
    except sqlite3.OperationalError as e:
        print("Error connecting to database:", e)
    else:
        f = open('phones.txt', 'r')
        phones = [x for x in f.read().split()]
        f.close()
        print('adding numbers to database...')
        rule = re.compile(r'^(8|\+7|7)\d{10}$')
        for i in phones:
            if not rule.match(i):
                key = i
                number = 0
            else:
                number = i
            if key != 0 and number != 0:
                print(f'getting information about number {number}')
                validNumber = validatePhoneNumber(number)
                data = getDataFromResponse(validNumber)
                print(f'adding number {number}')
                if not addPhoneToDB(con, validNumber, data, key):
                    return
        con.commit()
        print('done.')
        cur = con.execute('select * from phone_info')
        rows = cur.fetchall()
        csvWriter = csv.writer(open("output.csv", "w"))
        print("printing results to output.csv...")
        for row in rows:
            csvWriter.writerow(row)
        print("done.")
        con.close()

if __name__ == "__main__":
    getInfoAboutPhoneNumbersToCSV()