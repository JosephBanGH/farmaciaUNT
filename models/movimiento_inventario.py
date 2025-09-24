class Movimiento_inventario():
    def __init__(self,id,medicamento_id,tipo,cantidad,motivo,usuario_id,fecha_movimiento):
        self.id = id
        self.medicamento_id = medicamento_id
        self.tipo = tipo
        self.cantidad = cantidad
        self.motivo = motivo
        self.usuario_id = usuario_id
        self.fecha_movimiento = fecha_movimiento

