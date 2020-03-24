-- ============================================================================
--

-- ----------------------------------------------------------------------------
-- currencies as known by iso 4217
--
-- :id:   iso 4217 numeric code of the currency
-- :code: iso 4217 3 letter code of the currency
-- :name: iso 4217  long name of the currency
CREATE TABLE IF NOT EXISTS currency (
    id INT NOT NULL UNIQUE,
    code CHAR(3) NOT NULL UNIQUE,
    name VARCHAR(128) NOT NULL
);

-- ----------------------------------------------------------------------------
-- where does the data comes from
--
-- :name: a unique name for this source
-- :baseCurrency: in which currency does this source express the values
--
CREATE TABLE IF NOT EXISTS datasource (
    id BIGINT NOT NULL UNIQUE,
    name VARCHAR(128) NOT NULL UNIQUE,
    baseCurrency CHAR(3) REFERENCES currency(code)
);

-- ----------------------------------------------------------------------------
--
CREATE TABLE IF NOT EXISTS exchangeRates (
    at DATE NOT NULL,
    which CHAR(3) REFERENCES currency(code),
    inbase NUMERIC(10,10) NOT NULL
);
