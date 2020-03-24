'''
classes used for the CLI user interface
'''

from anyjson import deserialize
from eggcounter.api import ConfigurationException
from importlib import import_module
from logging import getLogger


class Command(object):

    def __init__(self, _options=None):
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


class CLIRunner(object):

    def __init__(self, options=None):
        '''
        :param dict<str, any> options: possible options to configure the system
        '''
        super().__init__()
        if options is None:
            options = {}
        self.configure(options)

    def configure(self, options):
        '''
        configure the Runner
        :param dict<str, any> options: the possible options.
        '''

    def run(self):
        pass


class SystemBootStraper(Command):

    def __init__(self, options=None):
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
            logger.debug(cmd)
            cursor.execute(cmd)
        self.commit()

    def _readAllCurrencyIds(self, cursor):
        '''
        returns all currencies by id (plus an empty one)
        '''
        cursor.execute('''
        SELECT id FROM currency
        UNION SELECT NULL;
        ''')
        return (x[0] for x in cursor.fetchall())

    def importCurrencies(self):
        logger = getLogger('database')
        logger.info('importing currencies')

        with open('./data/iso-4217-currency.json') as istream:
            currencies = deserialize(''.join(istream.readlines()))

        cursor = self._cursor()
        alreadyInserted = set(self._readAllCurrencyIds(cursor))
        for currency in currencies:

            if (currency['Withdrawal_Date'] is not None
                or currency['Withdrawal_Interval'] is not None):
                    # ignore currencies that have been withdrawn
                    continue
            numericCode = currency['Numeric_Code']
            numericCode = int(numericCode) if numericCode is not None else None
            if numericCode in alreadyInserted:
                # remove those without a numeric code and
                # remember that currencies can be used by multiple entities
                continue
            alreadyInserted.add(numericCode)
            try:
                cursor.execute('''
                INSERT INTO currency(id, code, name) VALUES(%s, %s, %s)
                ''', (
                    int(numericCode),
                    currency['Alphabetic_Code'],
                    currency['Currency']
                ))
            except Exception:
                logger.error(currency, exc_info=True)
                self.rollback()
                raise
        self.commit()
