# app/services/report.py - FIXED
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from datetime import datetime
import io

class ReportService:
    """PDF Report Generation - Professional validation reports"""
    
    @staticmethod
    def generate_validation_report(session, swab_results, rinse_results, maco_data, equipment_list=None):
        """Generate PDF validation report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=72)
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], 
                                     fontSize=18, spaceAfter=30, textColor=colors.HexColor('#1a472a'))
        heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'],
                                       fontSize=14, spaceAfter=12, textColor=colors.HexColor('#2d6a4f'))
        normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontSize=10)
        
        story = []
        
        # Header / Title
        story.append(Paragraph("Cleaning Validation Report", title_style))
        story.append(Paragraph(f"Session Code: {session.session_code}", normal_style))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%d-%b-%Y %H:%M')}", normal_style))
        story.append(Spacer(1, 20))
        
        # Product Information Section
        story.append(Paragraph("1. Product Information", heading_style))
        product_data = [
            ["Parameter", "Value"],
            ["Previous Product", session.previous_product.name if session.previous_product else "N/A"],
            ["Next Product", session.next_product.name if session.next_product else "N/A"],
            ["Previous Product Batch Size", f"{session.previous_product.min_batch_size} - {session.previous_product.max_batch_size} kg" if session.previous_product else "N/A"],
            ["Next Product Batch Size", f"{session.next_product.min_batch_size} - {session.next_product.max_batch_size} kg" if session.next_product else "N/A"],
            ["ADE/PDE", f"{session.previous_product.ade_pde} µg/day" if session.previous_product else "N/A"],
            ["Solubility", session.next_product.solubility if session.next_product else "N/A"],
            ["Cleaning Difficulty", session.next_product.hardest_to_clean if session.next_product else "N/A"],
        ]
        product_table = Table(product_data, colWidths=[3*inch, 4*inch])
        product_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(product_table)
        story.append(Spacer(1, 15))
        
        # MACO Calculation Section
        story.append(Paragraph("2. MACO Calculation Results", heading_style))
        maco_data_table = [
            ["Method", "Value (mg)", "Status"],
            ["10 ppm Method", f"{maco_data.get('10ppm', 0)}", "Calculated"],
            ["TDD Method", f"{maco_data.get('tdd', 0)}", "Calculated"],
            ["ADE/PDE Method", f"{maco_data.get('ade_pde', 0)}", "Calculated"],
            ["Lowest MACO Selected", f"{maco_data.get('lowest', 0)}", "CRITICAL VALUE"],
        ]
        maco_table = Table(maco_data_table, colWidths=[3*inch, 2*inch, 2*inch])
        maco_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#ffe0b2')),
            ('TEXTCOLOR', (0, 4), (-1, 4), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(maco_table)
        story.append(Spacer(1, 15))
        
        # Equipment Section (if equipment_list provided)
        if equipment_list:
            story.append(Paragraph("3. Equipment Details", heading_style))
            eq_data = [["Sr. No.", "Equipment Name", "ID", "Surface Area (m²)", "Used For"]]
            for idx, eq in enumerate(equipment_list, 1):
                eq_data.append([str(idx), eq.name, eq.equipment_id, str(eq.surface_area), eq.used_for])
            
            eq_table = Table(eq_data, colWidths=[0.75*inch, 1.5*inch, 1*inch, 1.2*inch, 2*inch])
            eq_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(eq_table)
            story.append(Spacer(1, 15))
        
        # Swab Results Section
        if swab_results:
            story.append(Paragraph("4. Swab Results", heading_style))
            swab_data = [["Location", "Result (ppm)", "Limit (ppm)", "Status"]]
            for r in swab_results:
                status_color = "Acceptable" if "Below LOQ" in str(r.reported) or float(r.result_ppm or 0) < 50 else "Review"
                swab_data.append([r.location_name, str(r.result_ppm or "N/A"), "50", status_color])
            
            swab_table = Table(swab_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1.5*inch])
            swab_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(swab_table)
            story.append(Spacer(1, 15))
        
        # Rinse Results Section
        if rinse_results:
            story.append(Paragraph("5. Rinse Results", heading_style))
            rinse_data = [["Equipment", "Rinse Volume (L)", "Result (ppm)", "Status"]]
            for r in rinse_results:
                status_color = "Acceptable" if "Below LOQ" in str(r.reported) else "Review"
                rinse_data.append([r.equipment_name, str(r.actual_rinse_volume), str(r.result_ppm or "N/A"), status_color])
            
            rinse_table = Table(rinse_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            rinse_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(rinse_table)
            story.append(Spacer(1, 15))
        
        # Conclusion / Signature Section
        story.append(Paragraph("6. Conclusion", heading_style))
        
        all_passed = all("Below LOQ" in str(r.reported) or float(r.result_ppm or 0) < 50 
                        for r in (swab_results or [])) if swab_results else True
        
        if all_passed:
            conclusion = "All swab and rinse results are within acceptable limits. The cleaning validation is PASSED."
            conclusion_color = colors.HexColor('#2d6a4f')
        else:
            conclusion = "Some results exceeded acceptable limits. Investigation required. The cleaning validation needs REVIEW."
            conclusion_color = colors.HexColor('#d32f2f')
        
        conclusion_style = ParagraphStyle('Conclusion', parent=styles['Normal'], 
                                          fontSize=12, textColor=conclusion_color, spaceAfter=20)
        story.append(Paragraph(conclusion, conclusion_style))
        
        story.append(Spacer(1, 30))
        story.append(Paragraph("_________________________", normal_style))
        story.append(Paragraph("Authorized Signatory", normal_style))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()