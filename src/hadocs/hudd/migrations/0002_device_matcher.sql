PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS device_identifiers (
  id INTEGER PRIMARY KEY,
  device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
  identifier_type TEXT NOT NULL COLLATE NOCASE,
  identifier_value TEXT NOT NULL COLLATE NOCASE,
  source_id INTEGER REFERENCES sources(id),
  UNIQUE(device_id, identifier_type, identifier_value)
);

CREATE INDEX IF NOT EXISTS idx_device_identifier_value
  ON device_identifiers(identifier_type, identifier_value);

INSERT OR REPLACE INTO metadata(key, value) VALUES ('schema_version', '0.2');
