-- ============================================================================
--
-- Notes:
--  * since the supported version of pg is 9.3
--    we cannot use the IF NOT EXISTS on index creation

-- ----------------------------------------------------------------------------
-- currencies as known by iso 4217
--
-- :id:   iso 4217 numeric code of the currency
-- :code: iso 4217 3 letter code of the currency
-- :name: iso 4217  long name of the currency
--
CREATE TABLE IF NOT EXISTS currency (
    id INTEGER NOT NULL UNIQUE,
    code CHAR(3) NOT NULL UNIQUE,
    name VARCHAR(128) NOT NULL,
    PRIMARY KEY (code)
);
CREATE INDEX currency_id_idx ON currency(id);

-- ----------------------------------------------------------------------------
-- where does the data comes from
--
-- :name: a unique name for this source
-- :baseCurrency: in which currency does this source express the values
--
CREATE TABLE IF NOT EXISTS datasource (
    id SERIAL NOT NULL UNIQUE,
    name VARCHAR(128) NOT NULL UNIQUE,
    baseCurrency CHAR(3) REFERENCES currency(code),
    PRIMARY KEY (id)
);

-- ----------------------------------------------------------------------------
-- exchange rate of a currency to the base currency at a certain date\
--
-- :at: which point in time
-- :which: currency is meant
-- :inbase: currency amount
--
CREATE TABLE IF NOT EXISTS exchangeRates (
    at DATE NOT NULL,
    which CHAR(3) REFERENCES currency(code),
    inbase NUMERIC(10,10) NOT NULL,
    PRIMARY KEY (which, at)
);

-- ----------------------------------------------------------------------------
-- meta informations about a security
--
-- :symbol: used globaly by the system
-- :name: the official name of the security
--
CREATE TABLE IF NOT EXISTS security (
    id SERIAL NOT NULL,
    symbol VARCHAR(16) NOT NULL UNIQUE,
    name VARCHAR(64) NOT NULL,
    PRIMARY KEY (id)
);
CREATE INDEX securityname ON security(name);

-- ----------------------------------------------------------------------------
-- which datasource provides which security information under which symbol
--
-- :security: which security is meant
-- :source: which dataSource is meant
-- :localSymbol: the symbol used by the source
--
CREATE TABLE IF NOT EXISTS security2source (
    security INTEGER NOT NULL REFERENCES security(id),
    source INTEGER NOT NULL REFERENCES dataSource(id),
    localSymbol VARCHAR(16) NOT NULL,
    PRIMARY KEY (security, source)
);
CREATE INDEX src2sec_idx ON security2source(source, security);

-- ----------------------------------------------------------------------------
-- the valuation of a security at a certain point in time
--
-- :at: which point in time is the valuation
-- :security: which is valuated
-- :open: opeing valuation
-- :high: the highest valuation for this date
-- :low: the lowest valuation for this date
-- :close:
-- :adjclose:
-- :volume:
--
CREATE TABLE IF NOT EXISTS valuation (
    at       DATE NOT NULL,
    security INTEGER NOT NULL REFERENCES security(id),
    open     MONEY NOT NULL,
    high     MONEY NOT NULL,
    low      MONEY NOT NULL,
    close    MONEY NOT NULL,
    adjclose MONEY NOT NULL,
    volume   INTEGER NOT NULL,
    PRIMARY KEY (security, at)
);
