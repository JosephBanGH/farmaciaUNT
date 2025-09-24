class Usuario:
    def __init__(self, id, username, password_hash, email, perfil, fecha_creacion, activo=True):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.perfil = perfil   # 'Administrador', 'Farmacéutico', 'Cajero' o 'Cliente'
        self.fecha_creacion = fecha_creacion
        self.activo = activo