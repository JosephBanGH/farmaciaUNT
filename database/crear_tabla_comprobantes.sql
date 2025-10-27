-- Script para crear la tabla de comprobantes
-- Este script debe ejecutarse en la base de datos farmacia_db

-- Crear tabla de comprobantes
CREATE TABLE IF NOT EXISTS comprobantes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    venta_id INT NOT NULL,
    tipo_comprobante ENUM('boleta', 'factura') NOT NULL,
    numero_comprobante VARCHAR(50) NOT NULL UNIQUE,
    ruta_archivo VARCHAR(255) NOT NULL,
    fecha_emision DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE,
    
    -- Índices para mejorar el rendimiento
    INDEX idx_venta_id (venta_id),
    INDEX idx_tipo_comprobante (tipo_comprobante),
    INDEX idx_fecha_emision (fecha_emision),
    INDEX idx_numero_comprobante (numero_comprobante),
    
    -- Relación con la tabla de ventas
    FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Comentarios sobre la tabla
ALTER TABLE comprobantes 
    COMMENT = 'Tabla para almacenar los comprobantes de pago emitidos (boletas y facturas)';

-- Verificar que la tabla se creó correctamente
DESCRIBE comprobantes;

-- Consulta de ejemplo para verificar
SELECT 'Tabla comprobantes creada exitosamente' AS mensaje;
