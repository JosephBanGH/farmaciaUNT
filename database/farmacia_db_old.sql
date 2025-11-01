-- Crear base de datos
CREATE DATABASE IF NOT EXISTS farmacia_db;
USE farmacia_db;

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    perfil ENUM('Administrador', 'Farmacéutico', 'Cajero', 'Cliente') NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE
);


-- Tabla de medicamentos
CREATE TABLE medicamentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    principio_activo VARCHAR(100),
    laboratorio VARCHAR(100),
    precio DECIMAL(10, 2) NOT NULL,
    stock INT NOT NULL DEFAULT 0,
    stock_minimo INT NOT NULL DEFAULT 10,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE
);

-- Tabla de movimientos de inventario
CREATE TABLE movimientos_inventario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    medicamento_id INT NOT NULL,
    tipo ENUM('entrada', 'salida') NOT NULL,
    cantidad INT NOT NULL,
    motivo VARCHAR(200),
    usuario_id INT NOT NULL,
    fecha_movimiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (medicamento_id) REFERENCES medicamentos(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de ventas
CREATE TABLE ventas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT,
    total DECIMAL(10, 2) NOT NULL,
    impuesto DECIMAL(10, 2) NOT NULL,
    usuario_id INT NOT NULL,
    fecha_venta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (cliente_id) REFERENCES usuarios(id)
);

-- Tabla de detalles de venta
CREATE TABLE detalles_venta (
    id INT AUTO_INCREMENT PRIMARY KEY,
    venta_id INT NOT NULL,
    medicamento_id INT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (venta_id) REFERENCES ventas(id),
    FOREIGN KEY (medicamento_id) REFERENCES medicamentos(id)
);

-- Tabla de proveedores
CREATE TABLE proveedores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    contacto VARCHAR(100),
    telefono VARCHAR(20),
    email VARCHAR(100),
    direccion TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE lotes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    medicamento_id INT NOT NULL,
    proveedor_id INT NOT NULL,
    numero_lote VARCHAR(50) NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    cantidad_inicial INT NOT NULL,
    cantidad_actual INT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (medicamento_id) REFERENCES medicamentos(id),
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
);
-- Procedimientos almacenados

-- SP para crear usuario
DELIMITER $$
CREATE PROCEDURE sp_crear_usuario(
    IN p_username VARCHAR(50),
    IN p_password_hash VARCHAR(255),
    IN p_email VARCHAR(100),
    IN p_perfil ENUM('Administrador', 'Farmacéutico', 'Cajero', 'Cliente')
)
BEGIN
    INSERT INTO usuarios (username, password_hash, email, perfil)
    VALUES (p_username, p_password_hash, p_email, p_perfil);
END$$
DELIMITER ;

-- SP para actualizar usuario
DELIMITER $$
CREATE PROCEDURE sp_actualizar_usuario(
    IN p_username VARCHAR(50),
    IN p_email VARCHAR(100),
    IN p_perfil ENUM('Administrador', 'Farmacéutico', 'Cajero', 'Cliente')
)
BEGIN
    UPDATE usuarios
    SET email=p_email, perfil=p_perfil
    where username=p_username;
END$$
DELIMITER ;

-- SP para actualizar stock
DELIMITER $$
CREATE PROCEDURE sp_actualizar_stock(
    IN p_medicamento_id INT,
    IN p_cantidad INT,
    IN p_tipo ENUM('entrada', 'salida'),
    IN p_motivo VARCHAR(200),
    IN p_usuario_id INT
)
BEGIN
    DECLARE current_stock INT;
    
    START TRANSACTION;
    
    -- Obtener stock actual
    SELECT stock INTO current_stock FROM medicamentos WHERE id = p_medicamento_id FOR UPDATE;
    
    -- Actualizar stock según el tipo de movimiento
    IF p_tipo = 'entrada' THEN
        UPDATE medicamentos SET stock = current_stock + p_cantidad WHERE id = p_medicamento_id;
    ELSE
        IF current_stock >= p_cantidad THEN
            UPDATE medicamentos SET stock = current_stock - p_cantidad WHERE id = p_medicamento_id;
        ELSE
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Stock insuficiente';
        END IF;
    END IF;
    
    -- Registrar movimiento
    INSERT INTO movimientos_inventario (medicamento_id, tipo, cantidad, motivo, usuario_id)
    VALUES (p_medicamento_id, p_tipo, p_cantidad, p_motivo, p_usuario_id);
    
    COMMIT;
END$$
DELIMITER ;

-- SP para ingresar lote y registrar movimiento
DELIMITER $$
CREATE PROCEDURE sp_ingresar_lote(
    IN p_medicamento_id INT,
    IN p_proveedor_id INT,
    IN p_numero_lote VARCHAR(50),
    IN p_fecha_vencimiento DATE,
    IN p_cantidad_inicial INT,
    IN p_usuario_id INT
)
BEGIN
    DECLARE lote_id INT;

    START TRANSACTION;

    -- Insertar lote
    INSERT INTO lotes (medicamento_id, proveedor_id, numero_lote, fecha_vencimiento, cantidad_inicial, cantidad_actual)
    VALUES (p_medicamento_id, p_proveedor_id, p_numero_lote, p_fecha_vencimiento, p_cantidad_inicial, p_cantidad_inicial);

    SET lote_id = LAST_INSERT_ID();

    -- Actualizar stock del medicamento
    UPDATE medicamentos SET stock = stock + p_cantidad_inicial WHERE id = p_medicamento_id;

    -- Registrar movimiento de inventario
    INSERT INTO movimientos_inventario (medicamento_id, tipo, cantidad, motivo, usuario_id)
    VALUES (p_medicamento_id, 'entrada', p_cantidad_inicial, CONCAT('Ingreso de lote ', p_numero_lote), p_usuario_id);

    COMMIT;
END$$
DELIMITER ;

-- SP para generar venta
DELIMITER $$
CREATE PROCEDURE sp_generar_venta(
    IN p_cliente_id INT,
    IN p_usuario_id INT,
    IN p_detalles JSON
)
BEGIN
    DECLARE v_total DECIMAL(10, 2) DEFAULT 0;
    DECLARE v_impuesto DECIMAL(10, 2) DEFAULT 0;
    DECLARE v_venta_id INT;
    DECLARE i INT DEFAULT 0;
    DECLARE num_items INT;
    DECLARE medicamento_id INT;
    DECLARE cantidad INT;
    DECLARE precio DECIMAL(10, 2);
    
    -- Calcular número de items
    SET num_items = JSON_LENGTH(p_detalles);
    
    START TRANSACTION;
    
    -- Calcular total e impuesto
    WHILE i < num_items DO
        SET medicamento_id = JSON_EXTRACT(p_detalles, CONCAT('$[', i, '].medicamento_id'));
        SET cantidad = JSON_EXTRACT(p_detalles, CONCAT('$[', i, '].cantidad'));
        SET precio = JSON_EXTRACT(p_detalles, CONCAT('$[', i, '].precio'));
        
        SET v_total = v_total + (cantidad * precio);
        SET i = i + 1;
    END WHILE;
    
    SET v_impuesto = v_total * 0.16; -- 16% de impuesto
    
    -- Insertar venta
    INSERT INTO ventas (cliente_id, total, impuesto, usuario_id)
    VALUES (p_cliente_id, v_total, v_impuesto, p_usuario_id);
    
    SET v_venta_id = LAST_INSERT_ID();
    
    -- Insertar detalles de venta y actualizar stock
    SET i = 0;
    WHILE i < num_items DO
        SET medicamento_id = JSON_EXTRACT(p_detalles, CONCAT('$[', i, '].medicamento_id'));
        SET cantidad = JSON_EXTRACT(p_detalles, CONCAT('$[', i, '].cantidad'));
        SET precio = JSON_EXTRACT(p_detalles, CONCAT('$[', i, '].precio'));
        
        INSERT INTO detalles_venta (venta_id, medicamento_id, cantidad, precio_unitario, subtotal)
        VALUES (v_venta_id, medicamento_id, cantidad, precio, cantidad * precio);
        
        -- Actualizar stock y registrar movimiento
        CALL sp_actualizar_stock(medicamento_id, cantidad, 'salida', 'Venta', p_usuario_id);
        
        SET i = i + 1;
    END WHILE;
    
    COMMIT;
END$$
DELIMITER ;

-- SP para obtener reportes de ventas
DELIMITER $$
CREATE PROCEDURE sp_obtener_reportes_ventas(
    IN p_fecha_inicio DATE,
    IN p_fecha_fin DATE
)
BEGIN
    SELECT 
        v.id,
        v.fecha_venta,
        v.total,
        v.impuesto,
        u.username as vendedor,
        c.username as cliente
    FROM ventas v
    INNER JOIN usuarios u ON v.usuario_id = u.id
    LEFT JOIN usuarios c ON v.cliente_id = c.id
    WHERE DATE(v.fecha_venta) BETWEEN p_fecha_inicio AND p_fecha_fin
    ORDER BY v.fecha_venta DESC;
END$$
DELIMITER ;

-- SP para alertas de vencimiento
DELIMITER $$
CREATE PROCEDURE sp_alertas_vencimiento()
BEGIN
    SELECT 
        l.id AS lote_id,
        m.nombre AS medicamento,
        l.numero_lote,
        l.fecha_vencimiento,
        DATEDIFF(l.fecha_vencimiento, CURDATE()) AS dias_restantes
    FROM lotes l
    INNER JOIN medicamentos m ON l.medicamento_id = m.id
    WHERE l.fecha_vencimiento IS NOT NULL 
      AND l.fecha_vencimiento <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
    ORDER BY l.fecha_vencimiento ASC;
END$$
DELIMITER ;

-- Insertar datos de ejemplo

INSERT INTO medicamentos (nombre, descripcion, principio_activo, laboratorio, precio, stock, stock_minimo) VALUES
('Paracetamol 500mg', 'Analgésico y antipirético', 'Paracetamol', 'Genfar', 5.50, 100, 20),
('Ibuprofeno 400mg', 'Antiinflamatorio no esteroideo', 'Ibuprofeno', 'Bayer', 7.80, 50, 15),
('Amoxicilina 500mg', 'Antibiótico de amplio espectro', 'Amoxicilina', 'Pfizer', 12.90, 30, 10),
('Loratadina 10mg', 'Antihistamínico', 'Loratadina', 'Sanofi', 8.25, 80, 25);

INSERT INTO proveedores (nombre, contacto, telefono, email, direccion) VALUES
('Distribuidora Médica S.A.', 'Juan Pérez', '1234-5678', 'ventas@dmedical.com', 'Av. Principal 123, Ciudad'),
('Farmacéutica Nacional', 'María González', '8765-4321', 'contacto@farmanacional.com', 'Calle Secundaria 456, Ciudad');

INSERT INTO lotes(medicamento_id, proveedor_id, numero_lote, fecha_vencimiento, cantidad_inicial, cantidad_actual) VALUES
(1, 1, 'L001', '2024-12-31', 100, 100),
(2, 2, 'L002', '2025-06-30', 50, 50),
(3, 1, 'L003', '2024-11-30', 30, 30),
(4, 2, 'L004', '2025-01-15', 80, 80);