from io import BytesIO
from typing import Optional
from openpyxl import Workbook
from fpdf import FPDF
from repositories.reporte.ReporteRepositorio import ReportesRepositorio
from conection.conectionDb import con_cursor

class ReportesService:

    @staticmethod
    @con_cursor
    def generar_reporte(cur, tipo: str, formato: str, fecha_inicio: str, fecha_fin: str, sucursal_id: Optional[int]) -> tuple:
        # Aseguramos que fecha_fin cubra hasta el final del día
        fecha_inicio_full = f"{fecha_inicio} 00:00:00"
        fecha_fin_full = f"{fecha_fin} 23:59:59"

        # 1. Obtener los datos según el tipo
        if tipo == "ventas":
            datos = ReportesRepositorio.obtener_datos_ventas(cur, fecha_inicio_full, fecha_fin_full, sucursal_id)
            encabezados = ["ID", "Fecha Venta", "Sucursal", "Vendedor", "Total Venta"]
        elif tipo == "movimientos":
            datos = ReportesRepositorio.obtener_datos_movimientos(cur, fecha_inicio_full, fecha_fin_full, sucursal_id)
            encabezados = ["ID", "Fecha", "Sucursal", "Producto", "Tipo", "Cantidad", "Motivo"]
        elif tipo == "transferencias":
            datos = ReportesRepositorio.obtener_datos_transferencias(cur, fecha_inicio_full, fecha_fin_full, sucursal_id)
            encabezados = ["ID", "Fecha", "Estado", "Prioridad", "Origen", "Destino"]
        else:
            return {"error": "Tipo de reporte no válido"}, 400

        if not datos:
            return {"error": "No hay datos para el rango de fechas seleccionado"}, 404

        # 2. Generar el archivo en el formato solicitado
        if formato == "excel":
            stream = ReportesService._generar_excel(tipo, encabezados, datos)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"reporte_{tipo}.xlsx"
        elif formato == "pdf":
            stream = ReportesService._generar_pdf(tipo, encabezados, datos)
            media_type = "application/pdf"
            filename = f"reporte_{tipo}.pdf"
        else:
            return {"error": "Formato no válido"}, 400

        # Retornamos el archivo (stream), los metadatos y el código 200
        return {"stream": stream, "media_type": media_type, "filename": filename}, 200

    @staticmethod
    def _generar_excel(tipo: str, encabezados: list, datos: list) -> BytesIO:
        wb = Workbook()
        ws = wb.active
        ws.title = f"Reporte {tipo.capitalize()}"

        # Escribir encabezados
        ws.append(encabezados)

        # Escribir datos
        for fila in datos:
            # Convertimos los valores de los diccionarios a lista de strings/numeros
            valores = [str(val) if val is not None else "" for val in fila.values()]
            ws.append(valores)

        stream = BytesIO()
        wb.save(stream)
        stream.seek(0)
        return stream

    @staticmethod
    def _generar_pdf(tipo: str, encabezados: list, datos: list) -> BytesIO:
        pdf = FPDF(orientation="L") # Horizontal para que quepan las columnas
        pdf.add_page()
        
        # Título principal (Como solicitaste)
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Productos Fafa Technology", new_x="LMARGIN", new_y="NEXT", align="C")
        
        # Subtítulo (Tipo de reporte)
        pdf.set_font("Helvetica", "I", 12)
        pdf.cell(0, 10, f"Reporte de {tipo.capitalize()}", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(5)

        # Configurar ancho de columnas (Dinámico según la cantidad de encabezados)
        ancho_columna = 270 / len(encabezados) # 270mm aprox de ancho útil en Landscape
        
        # Encabezados de la tabla
        pdf.set_font("Helvetica", "B", 10)
        for enc in encabezados:
            pdf.cell(ancho_columna, 10, str(enc), border=1, align="C")
        pdf.ln()

        # Datos de la tabla
        pdf.set_font("Helvetica", "", 9)
        for fila in datos:
            for val in fila.values():
                texto = str(val)[:30] if val is not None else "" # Truncamos a 30 chars por celda
                pdf.cell(ancho_columna, 10, texto, border=1, align="C")
            pdf.ln()

        stream = BytesIO(pdf.output())
        stream.seek(0)
        return stream