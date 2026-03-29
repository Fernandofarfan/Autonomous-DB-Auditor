import io
from typing import List
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from app.db_engines.base import AuditFinding

def generate_pdf_report(findings: List[AuditFinding]) -> io.BytesIO:
    """
    Genera un archivo PDF en memoria utilizando los hallazgos (AuditFindings).
    Retorna un buffer (io.BytesIO) listo para streamearse vía HTTP o guardarse a disco.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    normal_style = styles['Normal']
    
    story = []
    
    # Portada
    story.append(Paragraph("🛡️ DBA-Sentinel: Reporte de Auditoría", title_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Este reporte resume todos los hallazgos de Seguridad y Rendimiento detectados. Total de hallazgos: {len(findings)}", normal_style))
    story.append(Spacer(1, 20))
    
    if not findings:
        story.append(Paragraph("¡Excelente! No hemos detectado hallazgos críticos de seguridad ni performance 😊.", normal_style))
    else:
        # Imprimimos cada hallazgo
        for f in findings:
            html_text = (
                f"<b>[{f.category}] Nivel: {f.severity} (Motor: {f.engine})</b><br/>"
                f"<b>Detalle:</b> {f.description}<br/>"
                f"<b>Recomendación SQL:</b> <i>{f.remediation_sql or 'N/A'}</i>"
            )
            story.append(Paragraph(html_text, normal_style))
            story.append(Spacer(1, 15))
            
    doc.build(story)
    buffer.seek(0)
    return buffer
