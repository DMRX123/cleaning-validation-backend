from sqlalchemy.orm import Session
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import io

from ..models.validation_report import ValidationReport
from ..models.swab_result import SwabResult
from ..models.rinse_result import RinseResult


class ReportGeneratorService:
    """Generate VALIDATION REPORT (Past Tense) with actual results"""
    
    @staticmethod
    def generate_report(db: Session, report_id: int) -> bytes:
        report = db.query(ValidationReport).filter(ValidationReport.id == report_id).first()
        if not report:
            raise ValueError("Report not found")
        
        session = report.session
        swab_results = db.query(SwabResult).filter(SwabResult.session_id == session.id).all()
        rinse_results = db.query(RinseResult).filter(RinseResult.session_id == session.id).all()
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=72)
        
        styles = ReportGeneratorService._get_styles()
        story = []
        
        # Title Page
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph("CLEANING VALIDATION REPORT", styles['ReportTitle']))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(f"Report No.: {report.report_number}", styles['Normal']))
        story.append(Paragraph(f"Session Code: {session.session_code}", styles['Normal']))
        story.append(Paragraph(f"Report Date: {report.report_date.strftime('%d-%b-%Y')}", styles['Normal']))
        story.append(Paragraph(f"Prepared By: {report.prepared_by}", styles['Normal']))
        story.append(PageBreak())
        
        # What We Did
        story.append(Paragraph("1. WHAT WE DID", styles['SectionHeading']))
        actions = [
            f"We selected {session.previous_product.name if session.previous_product else 'N/A'} as the previous product.",
            f"We calculated MACO using three methods. The lowest value of {session.lowest_maco:.2f} mg was selected.",
            f"We established a swab limit of {session.swab_limit_ppm:.2f} ppm and rinse limit of {session.rinse_limit_ppm:.2f} ppm.",
            f"We performed three consecutive cleaning validation runs.",
            f"We collected {report.total_swab_samples} swab samples and {report.total_rinse_samples} rinse samples.",
            f"We analyzed all samples using validated analytical methods."
        ]
        for action in actions:
            story.append(Paragraph(f"• {action}", styles['Normal']))
            story.append(Spacer(1, 0.05*inch))
        story.append(PageBreak())
        
        # Why We Did It
        story.append(Paragraph("2. WHY WE DID IT", styles['SectionHeading']))
        justifications = [
            f"Because cross-contamination from {session.previous_product.name if session.previous_product else 'N/A'} could impact patient safety.",
            f"Because the ADE/PDE value of {session.previous_product.ade_pde if session.previous_product else 0} µg/day requires strict control.",
            f"Because regulatory guidelines (ICH Q7, EU GMP Annex 15) mandate cleaning validation."
        ]
        for justification in justifications:
            story.append(Paragraph(f"• {justification}", styles['Normal']))
            story.append(Spacer(1, 0.05*inch))
        story.append(PageBreak())
        
        # Results
        story.append(Paragraph("3. RESULTS", styles['SectionHeading']))
        
        # Swab Results Table
        story.append(Paragraph("3.1 Swab Sample Results", styles['SubSectionHeading']))
        swab_data = [["Location", "Result (ppm)", "Limit (ppm)", "Status"]]
        for r in swab_results:
            status = "PASS" if (r.result_ppm and session.swab_limit_ppm and r.result_ppm <= session.swab_limit_ppm) else "FAIL"
            swab_data.append([r.location_name, f"{r.result_ppm:.2f}" if r.result_ppm else "N/A", f"{session.swab_limit_ppm:.2f}", status])
        
        swab_table = Table(swab_data, colWidths=[6*cm, 3*cm, 3*cm, 3*cm])
        swab_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(swab_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Rinse Results Table
        story.append(Paragraph("3.2 Rinse Sample Results", styles['SubSectionHeading']))
        rinse_data = [["Equipment", "Result (ppm)", "Limit (ppm)", "Status"]]
        for r in rinse_results:
            status = "PASS" if (r.result_ppm and session.rinse_limit_ppm and r.result_ppm <= session.rinse_limit_ppm) else "FAIL"
            rinse_data.append([r.equipment_name, f"{r.result_ppm:.2f}", f"{session.rinse_limit_ppm:.2f}", status])
        
        rinse_table = Table(rinse_data, colWidths=[6*cm, 3*cm, 3*cm, 3*cm])
        rinse_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(rinse_table)
        story.append(PageBreak())
        
        # Conclusion
        story.append(Paragraph("4. CONCLUSION", styles['SectionHeading']))
        if report.overall_pass:
            conclusion_text = f"We successfully completed the cleaning validation study. All {report.total_swab_samples} swab samples met the acceptance criteria. The cleaning procedure is VALIDATED."
            conclusion_color = colors.HexColor('#2d6a4f')
        else:
            conclusion_text = f"The cleaning validation study did NOT meet acceptance criteria. {report.passed_swab_samples} out of {report.total_swab_samples} swab samples passed. Investigation and re-validation are REQUIRED."
            conclusion_color = colors.HexColor('#d32f2f')
        
        story.append(Paragraph(conclusion_text, ParagraphStyle('Conclusion', parent=styles['Normal'], textColor=conclusion_color)))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    @staticmethod
    def _get_styles():
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle('ReportTitle', parent=styles['Heading1'], fontSize=18, alignment=TA_CENTER, spaceAfter=30, textColor=colors.HexColor('#1a472a')))
        styles.add(ParagraphStyle('SectionHeading', parent=styles['Heading2'], fontSize=14, spaceAfter=12, textColor=colors.HexColor('#2d6a4f')))
        styles.add(ParagraphStyle('SubSectionHeading', parent=styles['Heading3'], fontSize=12, spaceAfter=8, textColor=colors.HexColor('#40916c')))
        return styles
    
    @staticmethod
    def generate_conclusion(session, overall_pass, passed_swab, total_swab):
        if overall_pass:
            return f"Cleaning validation study PASSED. All {total_swab} swab samples met the acceptance criteria."
        else:
            return f"Cleaning validation study FAILED. {passed_swab} out of {total_swab} swab samples passed. Investigation required."