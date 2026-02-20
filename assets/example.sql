SELECT
        td.id AS "ID Nota Fiscal",
        td.number AS "Número da Nota",
        STRING_AGG(DISTINCT i.purchase_order, ', ') AS "Pedidos de Compra",
        td.supplier_identification_number AS "CNPJ Fornecedor",
        city_fornecedor.name AS "Cidade Fornecedor",
        td.customer_identification_number AS "CNPJ Tomador",
        city_tomador.name AS "Cidade Tomador",
        TO_CHAR(t.completed_at, 'DD/MM/YYYY') AS "Data Escrituração"
    FROM tax_documents td
    INNER JOIN tasks t ON td.process_instance_id = t.process_instance_id
    INNER JOIN cities city_fornecedor ON td.supplier_city_id = city_fornecedor.id
    INNER JOIN cities city_tomador ON td.customer_city_id = city_tomador.id
    LEFT JOIN items i ON td.id = i.tax_document_id
    WHERE 
        td.type = 'MaterialInvoice'
        AND t.task_definition_id = 12
        AND t.status_id = 120
        AND t.completed_at >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
        AND t.completed_at < DATE_TRUNC('month', CURRENT_DATE)
    GROUP BY 
        td.id, td.number, td.supplier_identification_number, 
        city_fornecedor.name, td.customer_identification_number, 
        city_tomador.name, t.completed_at
    ORDER BY 
        t.completed_at DESC;