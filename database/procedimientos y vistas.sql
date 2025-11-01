use soft_farmacian

-- Procedimiento almacenado para crear un nuevo cliente
DELIMITER $$
CREATE PROCEDURE sp_crear_cliente(
    IN p_username VARCHAR(50),
    IN p_password_hash VARCHAR(255),
    IN p_email VARCHAR(100),
    IN p_nombres VARCHAR(100),
    IN p_apellidos VARCHAR(100),
    IN p_tipo_documento ENUM('DNI', 'RUC', 'CE', 'PASAPORTE'),
    IN p_numero_documento VARCHAR(20),
    IN p_direccion TEXT,
    IN p_telefono VARCHAR(20),
    IN p_fecha_nacimiento DATE,
    IN p_genero ENUM('Masculino', 'Femenino', 'Otro')
)
BEGIN
    DECLARE v_usuario_id INT;
    
    START TRANSACTION;
    
    -- Insertar en la tabla usuarios
    INSERT INTO usuarios(usuario, nombres, apellidos, contrasena_hash, email, perfil, activo)
    VALUES (p_username, p_nombres, p_apellidos, p_password_hash, p_email, 'Cliente', TRUE);
    
    SET v_usuario_id = LAST_INSERT_ID();
    
    -- Insertar en la tabla clientes
    INSERT INTO clientes (
        id, tipo_documento, numero_documento,
        direccion, telefono, fecha_nacimiento, genero
    ) VALUES (
        v_usuario_id, p_tipo_documento, p_numero_documento,
        p_direccion, p_telefono, p_fecha_nacimiento, p_genero
    );
    COMMIT;
END$$
DELIMITER ;

DELIMITER $$
CREATE PROCEDURE sp_actualizar_cliente(
    IN p_id INT,
    IN p_email VARCHAR(100),
    IN p_nombres VARCHAR(100),
    IN p_apellidos VARCHAR(100),
    IN p_direccion TEXT,
    IN p_telefono VARCHAR(20),
    IN p_fecha_nacimiento DATE,
    IN p_genero ENUM('Masculino', 'Femenino', 'Otro'),
    IN p_activo BOOLEAN
)
BEGIN
    START TRANSACTION;
    
    -- Actualizar datos en usuarios
    UPDATE usuarios 
    SET email = p_email,
        activo = p_activo,
        nombres = p_nombres,
        apellidos = p_apellidos
    WHERE id = p_id;
    
    -- Actualizar datos en clientes
    UPDATE clientes
    SET 
        direccion = p_direccion,
        telefono = p_telefono,
        fecha_nacimiento = p_fecha_nacimiento,
        genero = p_genero
    WHERE id = p_id;
    
    COMMIT;
END$$
DELIMITER ;


-- SP para crear usuario
DELIMITER $$
CREATE PROCEDURE sp_crear_usuario(
    IN p_username VARCHAR(50),
    IN p_nombres VARCHAR(50),
    IN p_apellidos VARCHAR(50),
    IN p_password_hash VARCHAR(255),
    IN p_email VARCHAR(100),
    IN p_perfil ENUM('Administrador', 'Farmacéutico', 'Cajero', 'Cliente')
)
BEGIN
    INSERT INTO usuarios (usuario, nombres, apellidos, contrasena_hash, email, perfil)
    VALUES (p_username, p_nombres, p_apellidos, p_password_hash, p_email, p_perfil);
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
    where usuario=p_username;
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
    IN p_precio_c DOUBLE,
    IN p_cantidad_inicial INT,
    IN p_usuario_id INT
)
BEGIN
    DECLARE lote_id INT;

    START TRANSACTION;

    -- Insertar lote
    INSERT INTO lotes (medicamento_id, proveedor_id, numero_lote, fecha_vencimiento, precio_compra, cantidad_inicial, cantidad_actual)
    VALUES (p_medicamento_id, p_proveedor_id, p_numero_lote, p_fecha_vencimiento, p_precio_c, p_cantidad_inicial, p_cantidad_inicial);

    SET lote_id = LAST_INSERT_ID();

    -- Actualizar stock del medicamento
    -- UPDATE medicamentos SET stock = stock + p_cantidad_inicial WHERE id = p_medicamento_id;

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
        u.usuario as vendedor,
        c.nombres as cliente
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

-- Vista para obtener información completa de clientes
CREATE OR REPLACE VIEW vista_clientes AS
SELECT 
    u.id,
    u.usuario,
    u.email,
    u.fecha_creacion,
    u.activo,
    u.nombres,
    u.apellidos,
    CONCAT(u.nombres, ' ', u.apellidos) as nombre_completo,
    c.tipo_documento,
    c.numero_documento,
    c.direccion,
    c.telefono,
    c.fecha_nacimiento,
    c.genero,
    c.puntos_acumulados
FROM usuarios u
JOIN clientes c ON u.id = c.id
WHERE u.perfil = 'Cliente';

-- Insertar proveedores
INSERT INTO `proveedores` (`nombre`, `contacto`, `telefono`, `email`, `direccion`, `ruc`, `activo`) VALUES
('Farmacéutica Nacional S.A.', 'Juan Pérez', '987654321', 'jperez@farmaceutica.com', 'Av. Principal 123, Lima', '20123456789', 1),
('Laboratorios Salud S.A.C.', 'María Gómez', '987654322', 'mgomez@salud.com', 'Calle Los Pinos 456, Lima', '20123456780', 1),
('Distribuidora Médica E.I.R.L.', 'Carlos López', '987654323', 'clopez@dime.com.pe', 'Jr. San Martín 789, Lima', '20123456781', 1);


