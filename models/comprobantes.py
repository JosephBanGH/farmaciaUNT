"""
Módulo para la generación de comprobantes de pago (Boletas y Facturas)
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas
from datetime import datetime
import os
import io


class GeneradorComprobantes:
    """Clase para generar comprobantes de pago en formato PDF"""
    
    def __init__(self):
        self.empresa = {
            'nombre': 'FARMACIA UNT',
            'ruc': '20123456789',
            'direccion': 'Av. América Sur 123, Trujillo - La Libertad',
            'telefono': '(044) 123-4567',
            'email': 'ventas@farmaciannt.com'
        }
    
    def generar_numero_comprobante(self, tipo, numero):
        """
        Genera el número de comprobante formateado
        tipo: 'B' para Boleta, 'F' para Factura
        """
        serie = f"B001" if tipo == 'B' else f"F001"
        return f"{serie}-{str(numero).zfill(8)}"
    
    def generar_boleta(self, venta_id, numero_boleta, cliente_nombre, detalles, total, fecha=None):
        """
        Genera una boleta de venta en formato PDF
        """
        if fecha is None:
            fecha = datetime.now()
        
        # Crear buffer en memoria
        buffer = io.BytesIO()
        
        # Crear el PDF
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elementos = []
        
        # Estilos
        styles = getSampleStyleSheet()
        titulo_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2E86AB'),
            spaceAfter=30,
            alignment=1  # Centrado
        )
        
        # Encabezado de la empresa
        elementos.append(Paragraph(self.empresa['nombre'], titulo_style))
        elementos.append(Paragraph(f"RUC: {self.empresa['ruc']}", styles['Normal']))
        elementos.append(Paragraph(self.empresa['direccion'], styles['Normal']))
        elementos.append(Paragraph(f"Tel: {self.empresa['telefono']} | Email: {self.empresa['email']}", styles['Normal']))
        elementos.append(Spacer(1, 0.3*inch))
        
        # Tipo de comprobante
        boleta_style = ParagraphStyle(
            'Boleta',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#A23B72'),
            alignment=1
        )
        numero_comprobante = self.generar_numero_comprobante('B', numero_boleta)
        elementos.append(Paragraph(f"BOLETA DE VENTA ELECTRÓNICA", boleta_style))
        elementos.append(Paragraph(f"{numero_comprobante}", boleta_style))
        elementos.append(Spacer(1, 0.3*inch))
        
        # Información del cliente y venta
        info_data = [
            ['Fecha:', fecha.strftime('%d/%m/%Y %H:%M:%S'), 'Venta N°:', str(venta_id)],
            ['Cliente:', cliente_nombre, '', '']
        ]
        
        info_table = Table(info_data, colWidths=[1.5*inch, 3*inch, 1.5*inch, 1.5*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F4F8')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#E8F4F8')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        elementos.append(info_table)
        elementos.append(Spacer(1, 0.3*inch))
        
        # Detalle de productos
        detalle_data = [['Cant.', 'Descripción', 'P. Unit.', 'Subtotal']]
        
        for item in detalles:
            detalle_data.append([
                str(item['cantidad']),
                item['nombre'],
                f"S/ {item['precio']:.2f}",
                f"S/ {item['cantidad'] * item['precio']:.2f}"
            ])
        
        detalle_table = Table(detalle_data, colWidths=[1*inch, 4*inch, 1.5*inch, 1.5*inch])
        detalle_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        elementos.append(detalle_table)
        elementos.append(Spacer(1, 0.2*inch))
        
        # Total
        total_data = [
            ['', '', 'TOTAL:', f"S/ {total:.2f}"]
        ]
        
        total_table = Table(total_data, colWidths=[1*inch, 4*inch, 1.5*inch, 1.5*inch])
        total_table.setStyle(TableStyle([
            ('BACKGROUND', (2, 0), (-1, 0), colors.HexColor('#2E86AB')),
            ('TEXTCOLOR', (2, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (2, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (2, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (2, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (2, 0), (-1, 0), 12),
        ]))
        elementos.append(total_table)
        elementos.append(Spacer(1, 0.5*inch))
        
        # Pie de página
        elementos.append(Paragraph("Gracias por su compra", styles['Normal']))
        elementos.append(Paragraph("Este documento es una representación impresa de la Boleta Electrónica", 
                                  styles['Italic']))
        
        # Construir PDF
        doc.build(elementos)
        
        # Obtener el PDF del buffer
        pdf = buffer.getvalue()
        buffer.close()
        
        return pdf
    
    def generar_factura(self, venta_id, numero_factura, cliente_datos, detalles, subtotal, igv, total, fecha=None):
        """
        Genera una factura en formato PDF
        cliente_datos debe incluir: nombre, ruc, direccion
        """
        if fecha is None:
            fecha = datetime.now()
        
        # Crear buffer en memoria
        buffer = io.BytesIO()
        
        # Crear el PDF
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elementos = []
        
        # Estilos
        styles = getSampleStyleSheet()
        titulo_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2E86AB'),
            spaceAfter=30,
            alignment=1
        )
        
        # Encabezado de la empresa
        elementos.append(Paragraph(self.empresa['nombre'], titulo_style))
        elementos.append(Paragraph(f"RUC: {self.empresa['ruc']}", styles['Normal']))
        elementos.append(Paragraph(self.empresa['direccion'], styles['Normal']))
        elementos.append(Paragraph(f"Tel: {self.empresa['telefono']} | Email: {self.empresa['email']}", styles['Normal']))
        elementos.append(Spacer(1, 0.3*inch))
        
        # Tipo de comprobante
        factura_style = ParagraphStyle(
            'Factura',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#F18F01'),
            alignment=1
        )
        numero_comprobante = self.generar_numero_comprobante('F', numero_factura)
        elementos.append(Paragraph(f"FACTURA ELECTRÓNICA", factura_style))
        elementos.append(Paragraph(f"{numero_comprobante}", factura_style))
        elementos.append(Spacer(1, 0.3*inch))
        
        # Información del cliente y venta
        info_data = [
            ['Fecha:', fecha.strftime('%d/%m/%Y %H:%M:%S'), 'Venta N°:', str(venta_id)],
            ['Señor(es):', cliente_datos.get('nombre', 'Cliente General'), '', ''],
            ['RUC:', cliente_datos.get('ruc', '-'), '', ''],
            ['Dirección:', cliente_datos.get('direccion', '-'), '', '']
        ]
        
        info_table = Table(info_data, colWidths=[1.5*inch, 3*inch, 1.5*inch, 1.5*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#FFF3E0')),
            ('BACKGROUND', (2, 0), (2, 0), colors.HexColor('#FFF3E0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        elementos.append(info_table)
        elementos.append(Spacer(1, 0.3*inch))
        
        # Detalle de productos
        detalle_data = [['Cant.', 'Descripción', 'P. Unit.', 'Subtotal']]
        
        for item in detalles:
            detalle_data.append([
                str(item['cantidad']),
                item['nombre'],
                f"S/ {item['precio']:.2f}",
                f"S/ {item['cantidad'] * item['precio']:.2f}"
            ])
        
        detalle_table = Table(detalle_data, colWidths=[1*inch, 4*inch, 1.5*inch, 1.5*inch])
        detalle_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F18F01')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        elementos.append(detalle_table)
        elementos.append(Spacer(1, 0.2*inch))
        
        # Totales
        total_data = [
            ['', '', 'SUBTOTAL:', f"S/ {subtotal:.2f}"],
            ['', '', 'IGV (18%):', f"S/ {igv:.2f}"],
            ['', '', 'TOTAL:', f"S/ {total:.2f}"]
        ]
        
        total_table = Table(total_data, colWidths=[1*inch, 4*inch, 1.5*inch, 1.5*inch])
        total_table.setStyle(TableStyle([
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (2, 0), (2, 1), 'Helvetica'),
            ('FONTNAME', (2, 2), (-1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (2, 0), (-1, 1), 11),
            ('FONTSIZE', (2, 2), (-1, 2), 14),
            ('BACKGROUND', (2, 2), (-1, 2), colors.HexColor('#F18F01')),
            ('TEXTCOLOR', (2, 2), (-1, 2), colors.whitesmoke),
            ('BOTTOMPADDING', (2, 0), (-1, -1), 12),
        ]))
        elementos.append(total_table)
        elementos.append(Spacer(1, 0.5*inch))
        
        # Pie de página
        elementos.append(Paragraph("Gracias por su compra", styles['Normal']))
        elementos.append(Paragraph("Este documento es una representación impresa de la Factura Electrónica", 
                                  styles['Italic']))
        elementos.append(Paragraph("Autorizado mediante Resolución de Superintendencia N° 123-2024/SUNAT", 
                                  styles['Italic']))
        
        # Construir PDF
        doc.build(elementos)
        
        # Obtener el PDF del buffer
        pdf = buffer.getvalue()
        buffer.close()
        
        return pdf
    
    def guardar_comprobante(self, pdf_bytes, tipo, numero, directorio='comprobantes'):
        """
        Guarda el comprobante PDF en el sistema de archivos
        """
        # Crear directorio si no existe
        if not os.path.exists(directorio):
            os.makedirs(directorio)
        
        # Generar nombre de archivo
        fecha = datetime.now().strftime('%Y%m%d')
        numero_formateado = self.generar_numero_comprobante(tipo, numero)
        nombre_archivo = f"{tipo}_{numero_formateado}_{fecha}.pdf"
        ruta_completa = os.path.join(directorio, nombre_archivo)
        
        # Guardar archivo
        with open(ruta_completa, 'wb') as f:
            f.write(pdf_bytes)
        
        return ruta_completa
