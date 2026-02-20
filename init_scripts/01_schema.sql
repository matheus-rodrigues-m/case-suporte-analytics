CREATE TABLE states (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255)
);

CREATE TABLE cities (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255),
    state_id BIGINT REFERENCES states(id)
);

CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255)
);

CREATE TABLE task_definitions (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255)
);

CREATE TABLE status (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255)
);

CREATE TABLE billing_reports (
    id BIGINT PRIMARY KEY,
    total_value DOUBLE PRECISION,
    supplier_identification_number VARCHAR(255),
    customer_identification_number VARCHAR(255)
);

CREATE TABLE process_instances (
    id BIGINT PRIMARY KEY,
    type VARCHAR(255)
);

CREATE TABLE tax_documents (
    id BIGINT PRIMARY KEY,
    number BIGINT,
    type VARCHAR(255), -- Ex: 'MaterialInvoice', 'ServiceInvoice'
    total_value DOUBLE PRECISION,
    supplier_identification_number VARCHAR(255), -- CNPJ Fornecedor
    customer_identification_number VARCHAR(255), -- CNPJ Tomador
    supplier_state_id BIGINT REFERENCES states(id),
    customer_state_id BIGINT REFERENCES states(id),
    supplier_city_id BIGINT REFERENCES cities(id),
    customer_city_id BIGINT REFERENCES cities(id),
    process_instance_id BIGINT REFERENCES process_instances(id)
);

CREATE TABLE items (
    id BIGINT PRIMARY KEY,
    description VARCHAR(255),
    unit_price DOUBLE PRECISION,
    total_value DOUBLE PRECISION,
    purchase_order VARCHAR(255), -- Campo solicitado no relatório
    tax_document_id BIGINT REFERENCES tax_documents(id)
);

CREATE TABLE tasks (
    id BIGINT PRIMARY KEY,
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    -- BIGINT para funcionar a FK com task_definitions(id)
    task_definition_id BIGINT REFERENCES task_definitions(id),
    status_id BIGINT REFERENCES status(id),
    assing_to_id BIGINT REFERENCES users(id),
    completed_by_id BIGINT REFERENCES users(id),
    process_instance_id BIGINT REFERENCES process_instances(id)
);