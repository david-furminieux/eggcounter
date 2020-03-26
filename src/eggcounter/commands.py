'''
classes used for the CLI user interface
'''

from anyjson import deserialize
from eggcounter.api import ConfigurationException
from importlib import import_module
from logging import getLogger
from re import compile

class Command(object):

    def __init__(self, _options):
        super().__init__()
        self._confPath = './etc'
        self._driver = None
        self._connection = None

    def run(self):
        raise NotImplementedError(type(self))

    def _run(self):
        self.readConfiguration()
        self._reconnect()

    def readConfiguration(self):

        with open(self._confPath + '/' + 'eggcounter.json') as stream:
            buff = ''.join(stream.readlines())
        self._config = deserialize(buff)

        if 'version' in self._config:
            try:
                _version = float(self._config['version'])
            except Exception as e:
                raise ConfigurationException('version must be numeric', e)

    def _reconnect(self):
        logger = getLogger('database')
        # get the driver
        connParams = dict(self._config['dbConnection'])
        drvName = connParams['driver']
        del connParams['driver']
        logger.info('loading the driver')
        try:
            self._driver = import_module(drvName)
        except Exception:
            logger.error('unable to load database driver', exc_info=True)
            raise

        logger.info('attempting connection to database with {}'.format(
            connParams))
        self._connection = self._driver.connect(**connParams)
        logger.info('connection established')

    def _cursor(self):
        if self._connection is None:
            self._reconnect()
        return self._connection.cursor()

    def commit(self):
        if self._connection is not None:
            self._connection.commit()

    def rollback(self):
        if self._connection is not None:
            self._connection.rollback()


class SystemBootStraper(Command):

    def __init__(self, options):
        super().__init__(options)

    def run(self):
        self._run()
        self.importSchema()
        self.importCurrencies()

    def importSchema(self):
        logger = getLogger('database')
        logger.info('importing schema')
        with open('./sql/schema.sql') as istream:
            schema = ''.join(istream.readlines())
        cmds = schema.split(';')
        cursor = self._cursor()
        for cmd in cmds:
            cmd = cmd.strip()
            if cmd == '':
                continue
            try:
                cursor.execute(cmd)
            except Exception:
                logger.error('while executing\n{}'.format(cmd), exc_info=True)
        self.commit()

    def _readAllCurrencyAndEntities(self, cursor):
        '''
        returns all currencies by id
        '''
        cursor.execute('''
            SELECT cur.code, ent.name
            FROM currency AS cur
            LEFT JOIN entity AS ent ON (ent.currency = cur.code)
        ''')
        lastCurrency = None
        countries = set()
        for cid, entity in cursor.fetchall():
            if lastCurrency != cid:
                yield lastCurrency, countries
                lastCurrency = cid
                countries = set()
            if entity is not None:
                countries.add(object)

        yield lastCurrency, countries

    def importCurrencies(self):
        logger = getLogger('database')
        logger.info('importing currencies')

        with open('./data/iso-4217-currency.json') as istream:
            currencies = deserialize(''.join(istream.readlines()))

        cursor = self._cursor()
        alreadyInserted = dict(self._readAllCurrencyAndEntities(cursor))
        countriesByCurrency = {}

        for currency in currencies:

            if (currency['Withdrawal_Date'] is not None
               or currency['Withdrawal_Interval'] is not None):
                # ignore currencies that have been withdrawn
                continue
            code = currency['Alphabetic_Code']

            entity = currency['Entity'].lower()
            try:
                tmp = countriesByCurrency[code]
            except KeyError:
                tmp = set()
                countriesByCurrency[code] = tmp
            tmp.add(entity)

            if code in alreadyInserted:
                # remove those without a numeric code and
                # remember that currencies can be used by multiple entities
                continue
            alreadyInserted[code] = set()
            try:
                cursor.execute('''
                INSERT INTO currency(id, code, name) VALUES(%s, %s, %s)
                ''', (
                    int(currency['Numeric_Code']),
                    code,
                    currency['Currency']
                ))
            except Exception:
                logger.error(currency, exc_info=True)
                self.rollback()
                raise

        for currency, countries in countriesByCurrency.items():
            for country in countries - alreadyInserted.get(currency, set()):
                # since we have country with more than one currency
                # only take the first
                cursor.execute('''
                    SELECT name FROM entity WHERE name = %s
                ''', (
                    country,
                ))
                if not cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO entity(name, currency) VALUES(%s, %s)
                    ''', (
                        country, currency
                    ))

        self.commit()


class TearDownCommand(Command):

    def __init__(self, options):
        super().__init__(options)

    def run(self):
        self._run()
        self.removeAllTables()

    def removeAllTables(self):
        logger = getLogger('database')
        logger.info('importing schema')
        with open('./sql/schema.sql') as istream:
            schema = ''.join(istream.readlines())
        cmds = schema.split(';')

        rexp = compile('CREATE\sTABLE\s(\w+)\s\(')

        tables = []
        for cmd in cmds:
            res = rexp.search(cmd)
            if res is not None:
                tables.append(res.group(1))

        cursor = self._cursor()
        cursor.execute('DROP TABLE ' + ','.join(tables))
        self.commit()
