PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS metadata (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sources (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  url TEXT,
  version TEXT,
  retrieved_at TEXT,
  license TEXT,
  UNIQUE(name, version)
);

CREATE TABLE IF NOT EXISTS categories (
  id INTEGER PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS organizations (
  id INTEGER PRIMARY KEY,
  hudd_id TEXT UNIQUE,
  canonical_name TEXT NOT NULL COLLATE NOCASE,
  normalized_name TEXT NOT NULL UNIQUE,
  entity_type TEXT NOT NULL DEFAULT 'brand'
    CHECK(entity_type IN ('manufacturer','brand','subbrand','group','platform','project','unknown')),
  category_id INTEGER REFERENCES categories(id),
  connection_class TEXT NOT NULL DEFAULT 'UKENDT',
  notes TEXT,
  review_status TEXT NOT NULL DEFAULT 'seed'
    CHECK(review_status IN ('seed','verified','needs_review','deprecated')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS organization_aliases (
  id INTEGER PRIMARY KEY,
  organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  alias TEXT NOT NULL COLLATE NOCASE,
  normalized_alias TEXT NOT NULL,
  alias_type TEXT NOT NULL DEFAULT 'name',
  UNIQUE(organization_id, normalized_alias)
);

CREATE TABLE IF NOT EXISTS organization_relations (
  id INTEGER PRIMARY KEY,
  parent_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  child_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  relation_type TEXT NOT NULL CHECK(relation_type IN ('owns','subbrand','product_brand','platform','oem','former_name','related')),
  source_id INTEGER REFERENCES sources(id),
  confidence TEXT NOT NULL DEFAULT 'seed' CHECK(confidence IN ('verified','high','medium','low','seed')),
  valid_from TEXT,
  valid_to TEXT,
  notes TEXT,
  UNIQUE(parent_id, child_id, relation_type)
);

CREATE TABLE IF NOT EXISTS support_codes (
  id INTEGER PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  label TEXT NOT NULL,
  description TEXT
);

CREATE TABLE IF NOT EXISTS organization_support (
  organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  support_code_id INTEGER NOT NULL REFERENCES support_codes(id) ON DELETE CASCADE,
  qualifier TEXT,
  source_id INTEGER REFERENCES sources(id),
  PRIMARY KEY(organization_id, support_code_id, qualifier)
);

CREATE TABLE IF NOT EXISTS protocols (
  id INTEGER PRIMARY KEY,
  slug TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS integrations (
  id INTEGER PRIMARY KEY,
  slug TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  integration_type TEXT NOT NULL DEFAULT 'unknown',
  domain TEXT,
  url TEXT
);

CREATE TABLE IF NOT EXISTS devices (
  id INTEGER PRIMARY KEY,
  hudd_id TEXT UNIQUE,
  manufacturer_id INTEGER REFERENCES organizations(id),
  brand_id INTEGER REFERENCES organizations(id),
  product_name TEXT NOT NULL,
  model TEXT,
  hardware_revision TEXT,
  region TEXT,
  product_family TEXT,
  gtin TEXT,
  manufacturer_device_id TEXT,
  description TEXT,
  lifecycle_status TEXT NOT NULL DEFAULT 'unknown',
  review_status TEXT NOT NULL DEFAULT 'seed',
  UNIQUE(brand_id, model, hardware_revision, region)
);

CREATE TABLE IF NOT EXISTS device_aliases (
  id INTEGER PRIMARY KEY,
  device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
  alias TEXT NOT NULL COLLATE NOCASE,
  alias_type TEXT NOT NULL DEFAULT 'name',
  UNIQUE(device_id, alias)
);

CREATE TABLE IF NOT EXISTS device_protocols (
  device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
  protocol_id INTEGER NOT NULL REFERENCES protocols(id),
  role TEXT NOT NULL DEFAULT 'native',
  notes TEXT,
  PRIMARY KEY(device_id, protocol_id, role)
);

CREATE TABLE IF NOT EXISTS device_integrations (
  device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
  integration_id INTEGER NOT NULL REFERENCES integrations(id),
  support_level TEXT NOT NULL DEFAULT 'unknown',
  local_operation TEXT NOT NULL DEFAULT 'unknown',
  requires_cloud INTEGER,
  requires_account INTEGER,
  requires_hub INTEGER,
  source_id INTEGER REFERENCES sources(id),
  verified_at TEXT,
  notes TEXT,
  PRIMARY KEY(device_id, integration_id)
);

CREATE TABLE IF NOT EXISTS source_records (
  id INTEGER PRIMARY KEY,
  source_id INTEGER NOT NULL REFERENCES sources(id),
  record_type TEXT NOT NULL,
  external_id TEXT,
  raw_name TEXT,
  raw_payload TEXT NOT NULL,
  payload_hash TEXT NOT NULL,
  imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(source_id, payload_hash)
);

CREATE INDEX IF NOT EXISTS idx_org_name ON organizations(canonical_name);
CREATE INDEX IF NOT EXISTS idx_org_category ON organizations(category_id);
CREATE INDEX IF NOT EXISTS idx_device_model ON devices(model);
CREATE INDEX IF NOT EXISTS idx_device_brand ON devices(brand_id);
CREATE INDEX IF NOT EXISTS idx_source_external ON source_records(source_id, external_id);

CREATE VIEW IF NOT EXISTS v_organization_overview AS
SELECT o.hudd_id, o.canonical_name, o.entity_type, c.name AS category,
       o.connection_class, o.review_status,
       GROUP_CONCAT(sc.code || COALESCE(':' || os.qualifier,''), ', ') AS support_codes,
       o.notes
FROM organizations o
LEFT JOIN categories c ON c.id=o.category_id
LEFT JOIN organization_support os ON os.organization_id=o.id
LEFT JOIN support_codes sc ON sc.id=os.support_code_id
GROUP BY o.id;

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
