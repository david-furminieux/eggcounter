from csv import reader
from datetime import datetime
import requests
import unittest
from urllib.parse import quote
from time import strptime
from bs4 import BeautifulSoup


class Yahoo(unittest.TestCase):

    def extractFloat(self, value):
        return None if value == 'null' else float(value)

    def extractInt(self, value):
        return None if value == 'null' else int(value)

    def extractSymbol(self, symbol, startDate=None, endDate=None):
        YAPI_URL = 'https://query1.finance.yahoo.com/v7/finance/download/'
        tmp = YAPI_URL + quote(symbol)

        if startDate is None:
            startDate = datetime.today()
        if endDate is None:
            endDate = datetime.today()

        response = requests.get(tmp, {
            'period1': int(startDate.strftime('%s')),
            'period2': int(endDate.strftime('%s')),
            'interval': '1d',
            'events': 'history'
        })
        first = True
        for row in reader(response.iter_lines(decode_unicode=True)):
            if first:
                first = False
                continue

            date, open_, high, low, close, adjclose, volume = row
            yield {
                'date': strptime(date, '%Y-%m-%d'),
                'open': self.extractFloat(open_),
                'high': self.extractFloat(high),
                'low': self.extractFloat(low),
                'close': self.extractFloat(close),
                'adjclose': self.extractFloat(adjclose),
                'volume': self.extractInt(volume)
            }

    def testSingleQuote(self):
        d1 = datetime(2019, 3, 23)
        d2 = datetime(2020, 3, 23)
        for elem in self.extractSymbol('^BFX', d1, d2):
            print(elem)

    def testGettingComponentsOfIndex(self):
        YAPI_URL = 'https://finance.yahoo.com/quote/{}/components'
        url = YAPI_URL.format(quote('^GDAXI'))

        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        for row in soup.find('tbody').find_all('tr'):
            first = True
            result = []
            for elem in row.find_all('td'):
                if first:
                    first = False
                    result.append(elem.a.string)
                else:
                    result.append(elem.string)
            print(result)

    def testGettingCurrency(self):
        d1 = datetime(2019, 3, 23)
        d2 = datetime(2020, 3, 23)
        for elem in self.extractSymbol('EURUSD=X', d1, d2):
            print(elem)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
