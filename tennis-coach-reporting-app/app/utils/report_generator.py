from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase.pdfmetrics import registerFontFamily

def create_single_report_pdf(report, output_buffer):
    """Create a single PDF report in the style of the tennis club template"""
    c = canvas.Canvas(output_buffer, pagesize=A4)
    width, height = A4
    
    # Header
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 50, "Tennis Coaching Report")
    
    # Student Info
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 100, f"Player: {report.student.name}")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 120, f"Coach: {report.coach.name}")
    c.drawString(50, height - 140, f"Term: {report.teaching_period.name}")
    c.drawString(50, height - 160, f"Group: {report.tennis_group.name}")
    
    # Skills Assessment
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 200, "Skills Assessment")
    
    y_position = height - 230
    c.setFont("Helvetica", 12)
    
    # Draw assessment items
    metrics = [
        ("Forehand", report.forehand),
        ("Backhand", report.backhand),
        ("Movement", report.movement)
    ]
    
    for metric, value in metrics:
        c.drawString(50, y_position, f"{metric}:")
        c.drawString(150, y_position, str(value))
        y_position -= 20
    
    # Overall Rating
    y_position -= 20
    c.drawString(50, y_position, "Overall Rating:")
    c.drawString(150, y_position, f"{report.overall_rating}/5")
    
    # Next Term Recommendation
    y_position -= 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_position, "Next Term Recommendation")
    c.setFont("Helvetica", 12)
    y_position -= 20
    c.drawString(50, y_position, report.next_group_recommendation)
    
    # Notes
    if report.notes:
        y_position -= 40
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_position, "Additional Notes")
        c.setFont("Helvetica", 12)
        y_position -= 20
        # Split notes into multiple lines if needed
        words = report.notes.split()
        line = []
        for word in words:
            line.append(word)
            if len(' '.join(line)) > 70:  # Limit line length
                c.drawString(50, y_position, ' '.join(line[:-1]))
                y_position -= 20
                line = [word]
        if line:
            c.drawString(50, y_position, ' '.join(line))
    
    # Footer with regular Helvetica instead of Italic
    c.setFont("Helvetica", 10)
    c.drawString(50, 50, f"Generated on {datetime.now().strftime('%Y-%m-%d')}")
    
    c.save()
    output_buffer.seek(0)