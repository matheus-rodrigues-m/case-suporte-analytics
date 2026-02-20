-- 1. Inserindo Dados Estáticos (Baseados no PDF)
INSERT INTO task_definitions (name, id) VALUES 
('Verificação de Nota Duplicada', 10),
('Verificação de Divergências na Nota', 11),
('Escrituração da Nota', 12), -- O alvo
('Pagamento da Nota', 13);

INSERT INTO status (name, id) VALUES
('Nota Duplicada', 100),
('Nota não é Duplicada', 101),
('Nota com Divergência', 110),
('Nota sem Divergência', 111),
('Nota Escriturada com Sucesso', 120), -- O alvo
('Nota não Escriturada', 121),
('Nota Paga', 130),
('Nota não Paga', 131);

INSERT INTO states (id, name) VALUES (1, 'Minas Gerais'), (2, 'São Paulo');
INSERT INTO cities (id, name, state_id) VALUES 
(1, 'Montes Claros', 1), 
(2, 'Belo Horizonte', 1),
(3, 'São Paulo', 2);

INSERT INTO users (id, name, email) VALUES (1, 'Analista Senior', 'analista@empresa.com');

-- CENÁRIO 1: O CASO PERFEITO:
-- Instância
INSERT INTO process_instances (id, type) VALUES (1001, 'Inbound');
-- Nota Fiscal (Material)
INSERT INTO tax_documents (id, number, type, total_value, supplier_identification_number, customer_identification_number, supplier_city_id, customer_city_id, process_instance_id) 
VALUES (501, 12345, 'MaterialInvoice', 1000.00, '11111111000111', '99999999000199', 1, 2, 1001);
-- Item (Único)
INSERT INTO items (id, description, unit_price, total_value, purchase_order, tax_document_id)
VALUES (1, 'Parafuso Aço', 1000.00, 1000.00, 'PO-2024-001', 501);
-- Tarefa (Escrituração - Sucesso - Mês Passado)
INSERT INTO tasks (id, created_at, completed_at, task_definition_id, status_id, process_instance_id)
VALUES (1, CURRENT_DATE - INTERVAL '1 month', CURRENT_DATE - INTERVAL '1 month', 12, 120, 1001);

-- CENÁRIO 2: O CASO DE MÚLTIPLOS ITENS (Deve aparecer com os itens agrupado)
INSERT INTO process_instances (id, type) VALUES (1002, 'Inbound');
INSERT INTO tax_documents (id, number, type, total_value, supplier_identification_number, customer_identification_number, supplier_city_id, customer_city_id, process_instance_id) 
VALUES (502, 67890, 'MaterialInvoice', 2000.00, '22222222000122', '99999999000199', 3, 1, 1002);
-- Item 1
INSERT INTO items (id, description, purchase_order, tax_document_id) VALUES (2, 'Martelo', 'PO-2024-002', 502);
-- Item 2 (Pedido diferente para testar o agrupamento)
INSERT INTO items (id, description, purchase_order, tax_document_id) VALUES (3, 'Pregos', 'PO-2024-003', 502);
-- Tarefa (Sucesso Mês Passado)
INSERT INTO tasks (id, created_at, completed_at, task_definition_id, status_id, process_instance_id)
VALUES (2, CURRENT_DATE - INTERVAL '1 month', CURRENT_DATE - INTERVAL '1 month', 12, 120, 1002);

-- CENÁRIO 3: FORA DA DATA (Não deve aparecer na consulta)
INSERT INTO process_instances (id, type) VALUES (1003, 'Inbound');
INSERT INTO tax_documents (id, type, process_instance_id) VALUES (503, 'MaterialInvoice', 1003);
INSERT INTO items (id, purchase_order, tax_document_id) VALUES (4, 'PO-OLD', 503);
-- Tarefa (Sucesso, mas há 3 meses atrás)
INSERT INTO tasks (id, completed_at, task_definition_id, status_id, process_instance_id)
VALUES (3, CURRENT_DATE - INTERVAL '3 months', 12, 120, 1003);

-- CENÁRIO 4: TIPO ERRADO (Serviço - Não deve aparecer)
INSERT INTO process_instances (id, type) VALUES (1004, 'Inbound');
INSERT INTO tax_documents (id, type, process_instance_id) VALUES (504, 'ServiceInvoice', 1004);
INSERT INTO items (id, purchase_order, tax_document_id) VALUES (5, 'PO-SERV', 504);
INSERT INTO tasks (id, completed_at, task_definition_id, status_id, process_instance_id)
VALUES (4, CURRENT_DATE - INTERVAL '1 month', 12, 120, 1004);

-- CENÁRIO 5: FALHA NA TAREFA (Não deve aparecer)
INSERT INTO process_instances (id, type) VALUES (1005, 'Inbound');
INSERT INTO tax_documents (id, type, process_instance_id) VALUES (505, 'MaterialInvoice', 1005);
INSERT INTO items (id, purchase_order, tax_document_id) VALUES (6, 'PO-FAIL', 505);
-- Tarefa (Escrituração, mas falhou - ID 121)
INSERT INTO tasks (id, completed_at, task_definition_id, status_id, process_instance_id)
VALUES (5, CURRENT_DATE - INTERVAL '1 month', 12, 121, 1005);