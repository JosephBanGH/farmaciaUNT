# CREATE TABLE movimientos_inventario (
#     id INT AUTO_INCREMENT PRIMARY KEY,
#     medicamento_id INT NOT NULL,
#     tipo ENUM('entrada', 'salida') NOT NULL,
#     cantidad INT NOT NULL,
#     motivo VARCHAR(200),
#     usuario_id INT NOT NULL,
#     fecha_movimiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#     FOREIGN KEY (medicamento_id) REFERENCES medicamentos(id),
#     FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
# );
class Movimiento_inventario():
    def __init__(self,id,medicamento_id,tipo,cantidad,motivo,usuario_id,fecha_movimiento):
        self.id = id
        self.medicamento_id = medicamento_id
        self.tipo = tipo
        self.cantidad = cantidad
        self.motivo = motivo
        self.usuario_id = usuario_id
        self.fecha_movimiento = fecha_movimiento

