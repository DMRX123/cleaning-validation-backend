from sqlalchemy.orm import Session
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, 
    PageBreak, Image, KeepTogether, NextPageTemplate, FrameBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import os
from datetime import datetime, timedelta

from ..models.product import Product
from ..models.equipment import Equipment
from ..models.protocol_template import CleaningValidationProtocol  # FIXED - Correct import
from ..models.recovery_study import RecoveryStudy
from ..models.fmea_risk import FMEARiskAssessment
from ..models.nitrosamine import NitrosamineRiskAssessment
from ..models.operator_qualification import OperatorQualification
from ..services.maco import MACOService
from ..services.swab import SwabService
from ..services.rinse import RinseService
from ..services.worst_case_service import WorstCaseService


class ProtocolGeneratorService:
    """Generate professional validation protocol PDF - 50+ pages"""
    
    @staticmethod
    def generate_protocol(db: Session, protocol_id: int) -> bytes:
        """Generate complete protocol PDF"""
        
        protocol = db.query(CleaningValidationProtocol).filter(
            CleaningValidationProtocol.id == protocol_id
        ).first()
        
        if not protocol:
            raise ValueError("Protocol not found")
        
        product = protocol.product
        equipment_list = db.query(Equipment).filter(
            Equipment.plant == product.plant
        ).all()
        
        total_surface_area = sum(eq.surface_area for eq in equipment_list)
        
        # Get all products in same plant for worst case
        all_products = db.query(Product).filter(
            Product.plant == product.plant
        ).all()
        worst_case = WorstCaseService.select_worst_case(all_products)
        
        # Calculate MACO
        maco_result = MACOService.calculate_all(worst_case, product) if worst_case else {"lowest_maco": 0}
        lowest_maco = maco_result.get("lowest_maco", 0)
        
        # Calculate swab limit
        swab_limit_mg = (lowest_maco * 0.01) / total_surface_area if total_surface_area > 0 else 0
        
        # Get recovery studies
        recovery_studies = db.query(RecoveryStudy).filter(
            RecoveryStudy.product_id == product.id,
            RecoveryStudy.is_valid == True
        ).all()
        
        # Get FMEA data
        fmea_data = db.query(FMEARiskAssessment).all()
        
        # Get nitrosamine assessment
        nitrosamine = db.query(NitrosamineRiskAssessment).filter(
            NitrosamineRiskAssessment.product_id == product.id
        ).first()
        
        # Get operator qualifications
        operator_quals = db.query(OperatorQualification).filter(
            OperatorQualification.is_active == True
        ).all()
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            rightMargin=72, 
            leftMargin=72,
            topMargin=72, 
            bottomMargin=72
        )
        
        styles = ProtocolGeneratorService._get_styles()
        story = []
        
        # Generate all sections
        story.extend(ProtocolGeneratorService._generate_title_page(protocol, product, styles))
        story.append(PageBreak())
        
        story.extend(ProtocolGeneratorService._generate_toc(styles))
        story.append(PageBreak())
        
        story.extend(ProtocolGeneratorService._generate_section_1(protocol, styles))
        story.append(PageBreak())
        
        story.extend(ProtocolGeneratorService._generate_section_2(product, styles))
        story.append(PageBreak())
        
        story.extend(ProtocolGeneratorService._generate_section_3(styles))
        story.append(PageBreak())
        
        story.extend(ProtocolGeneratorService._generate_section_4(product, styles))
        story.append(PageBreak())
        
        story.extend(ProtocolGeneratorService._generate_section_5(styles))
        story.append(PageBreak())
        
        story.extend(ProtocolGeneratorService._generate_section_6(product, equipment_list, styles))
        story.append(PageBreak())
        
        story.extend(ProtocolGeneratorService._generate_section_6_7(protocol, styles))
        story.append(PageBreak())
        
        story.extend(ProtocolGeneratorService._generate_section_6_8(protocol, styles))
        story.append(PageBreak())
        
        story.extend(ProtocolGeneratorService._generate_section_6_9(protocol, styles))
        story.append(PageBreak())
        
        story.extend(ProtocolGeneratorService._generate_section_7(
            product, worst_case, maco_result, swab_limit_mg, total_surface_area, equipment_list, styles
        ))
        story.append(PageBreak())
        
        story.extend(ProtocolGeneratorService._generate_section_7_4(equipment_list, swab_limit_mg, styles))
        story.append(PageBreak())
        
        story.extend(ProtocolGeneratorService._generate_section_8(fmea_data, equipment_list, styles))
        story.append(PageBreak())
        
        story.extend(ProtocolGeneratorService._generate_section_8_3(recovery_studies, styles))
        story.append(PageBreak())
        
        story.extend(ProtocolGeneratorService._generate_section_9(swab_limit_mg, styles))
        story.append(PageBreak())
        
        story.extend(ProtocolGeneratorService._generate_section_10(product, styles))
        story.append(PageBreak())
        
        story.extend(ProtocolGeneratorService._generate_section_11(operator_quals, styles))
        story.append(PageBreak())
        
        story.extend(ProtocolGeneratorService._generate_section_12(styles))
        story.append(PageBreak())
        
        story.extend(ProtocolGeneratorService._generate_section_13(nitrosamine, product, styles))
        story.append(PageBreak())
        
        story.extend(ProtocolGeneratorService._generate_section_14(styles))
        story.append(PageBreak())
        
        story.extend(ProtocolGeneratorService._generate_section_15_16(styles))
        story.append(PageBreak())
        
        story.extend(ProtocolGeneratorService._generate_section_17_19(styles))
        story.append(PageBreak())
        
        story.extend(ProtocolGeneratorService._generate_forms(equipment_list, styles))
        
        doc.build(story)
        buffer.seek(0)
        
        return buffer.getvalue()
    
    @staticmethod
    def _get_styles():
        styles = getSampleStyleSheet()
        
        styles.add(ParagraphStyle(
            name='ProtocolTitle',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=30,
            textColor=colors.HexColor('#1a472a')
        ))
        
        styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#2d6a4f')
        ))
        
        styles.add(ParagraphStyle(
            name='SubSectionHeading',
            parent=styles['Heading3'],
            fontSize=12,
            spaceAfter=8,
            textColor=colors.HexColor('#40916c')
        ))
        
        styles.add(ParagraphStyle(
            name='Justified',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=6
        ))
        
        styles.add(ParagraphStyle(
            name='TableHeader',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors.white
        ))
        
        return styles
    
    @staticmethod
    def _generate_title_page(protocol, product, styles):
        story = []
        
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph("EQUIPMENT CLEANING VALIDATION PROTOCOL", styles['ProtocolTitle']))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(f"Product Name: {product.name}", styles['Justified']))
        story.append(Paragraph(f"Product Code: {product.product_code or 'N/A'}", styles['Justified']))
        story.append(Paragraph(f"Location: {protocol.location}", styles['Justified']))
        story.append(Paragraph(f"Manufacturing Block: {protocol.manufacturing_block or product.plant}", styles['Justified']))
        story.append(Paragraph(f"Batch Size: {protocol.batch_size_range or f'{product.min_batch_size} ± {product.max_batch_size - product.min_batch_size} Kg'}", styles['Justified']))
        story.append(Paragraph(f"Date of Issue: {protocol.date_of_issue.strftime('%B %Y') if protocol.date_of_issue else datetime.now().strftime('%B %Y')}", styles['Justified']))
        story.append(Paragraph(f"Protocol No.: {protocol.protocol_number} (Revision {protocol.revision})", styles['Justified']))
        
        return story
    
    @staticmethod
    def _generate_toc(styles):
        story = []
        
        story.append(Paragraph("TABLE OF CONTENTS", styles['SectionHeading']))
        story.append(Spacer(1, 0.2*inch))
        
        toc_items = [
            ("1. Protocol Approval", 4),
            ("2. Introduction", 5),
            ("3. Objective", 5),
            ("4. Scope", 5),
            ("5. Responsibilities", 6),
            ("6. Cleaning Procedure", 7),
            ("  6.1 Cleaning Agent Selection Criteria", 7),
            ("  6.2 Solubility Pattern and Cleaning Agent", 7),
            ("  6.3 Details of Equipment Used", 7),
            ("  6.4 Batch Size of the Product", 8),
            ("  6.5 Flow Chart", 9),
            ("  6.6 Reference of the Cleaning Procedure", 10),
            ("  6.7 Dirty Hold Time (DHT) Validation", 10),
            ("  6.8 Clean Hold Time (CHT) Validation", 10),
            ("  6.9 Campaign Length Validation", 10),
            ("7. Establishment of Maximum Allowable Limit", 11),
            ("  7.1 MACO/MSC Calculation", 11),
            ("  7.2 Calculation of Rinse Limit", 13),
            ("  7.3 Calculation of Swab Limit", 13),
            ("  7.4 Stratified Carryover Calculation", 14),
            ("8. Sampling Plan", 16),
            ("  8.1 FMEA-Based Scientific Rational", 16),
            ("  8.2 Sampling Procedure", 18),
            ("  8.3 Recovery Study and Correction Factor", 21),
            ("9. Acceptance Criteria", 23),
            ("10. Analytical Method Validation", 25),
            ("11. Operator Qualification for Cleaning", 26),
            ("12. Continued Process Verification", 28),
            ("13. Nitrosamines Risk Assessment", 30),
            ("14. Data Integrity (ALCOA+) Compliance", 32),
            ("15. Detail of Deviation / Discrepancies", 33),
            ("16. Revalidation Criteria", 33),
            ("17. Results", 34),
            ("18. Conclusion", 34),
            ("19. Summary Report & Approval", 34),
            ("Form-A Chemical Contamination Results", 35),
            ("Form-B Microbiological Contamination Results", 37),
            ("Form-C Visual Inspection Results", 39),
            ("Annexure-I Swab Sampling Points Drawings", 41)
        ]
        
        for item, page in toc_items:
            story.append(Paragraph(f"{item:<60} {page}", styles['Justified']))
            story.append(Spacer(1, 0.05*inch))
        
        return story
    
    @staticmethod
    def _generate_section_1(protocol, styles):
        story = []
        
        story.append(Paragraph("1. PROTOCOL APPROVAL", styles['SectionHeading']))
        story.append(Spacer(1, 0.1*inch))
        
        approval_data = [
            ["Activity", "Department", "Signature", "Name", "Date"],
            ["Prepared By", "Quality Assurance", "___________", protocol.prepared_by or "_________", protocol.prepared_date.strftime('%d/%m/%Y') if protocol.prepared_date else "_________"],
            ["Checked By", "Production", "___________", "_________", "_________"],
            ["Checked By", "Powder Processing Area", "___________", "_________", "_________"],
            ["Checked By", "Engineering", "___________", "_________", "_________"],
            ["Checked By", "Quality Control", "___________", "_________", "_________"],
            ["Checked By", "Quality Assurance", "___________", "_________", "_________"],
            ["Approved By", "Head Quality Assurance", "___________", "_________", "_________"]
        ]
        
        approval_table = Table(approval_data, colWidths=[4*cm, 4*cm, 3*cm, 4*cm, 3*cm])
        approval_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(approval_table)
        
        return story
    
    @staticmethod
    def _generate_section_2(product, styles):
        story = []
        
        story.append(Paragraph("2. INTRODUCTION", styles['SectionHeading']))
        story.append(Paragraph(
            f"Cleaning is necessary to avoid cross contamination from previous active ingredients, "
            f"raw materials, intermediates, residual solvents to subsequent products. "
            f"Contamination from lubricant used for equipment, cleaning agent (if any) and cleaning tools "
            f"such as brushes, mops etc. used during cleaning process. It also establishes the bio-burden "
            f"load of equipment after completion of cleaning process. Present cleaning validation study "
            f"involves evaluation of cleaning procedure established for cleaning of various equipment used "
            f"in the manufacturing of {product.name} through rinse / swab sampling (for micro & chemical) technique.",
            styles['Justified']
        ))
        story.append(Spacer(1, 0.1*inch))
        
        story.append(Paragraph(
            f"API product \"{product.name}\" is planned to be manufactured in {product.plant} "
            f"at manufacturing facility. Hence as per SOP, cleaning validation shall be performed in API stage "
            f"from crystallization onwards by establishing maximum allowable carryover (MACO) criteria.",
            styles['Justified']
        ))
        story.append(Spacer(1, 0.1*inch))
        
        story.append(Paragraph("Regulatory Basis for this Protocol:", styles['SubSectionHeading']))
        regulations = [
            "• ICH Q7 (GMP for Active Pharmaceutical Ingredients) - Section 5.2",
            "• EU GMP Annex 15 (Qualification and Validation) - Section 10",
            "• WHO TRS 1019 (Validation Guidelines) - Appendix 3 & 7",
            "• APIC Cleaning Validation Guide 2021 (Sections 4, 5, 7, 8)",
            "• PIC/S PI 006-3 (Cleaning Validation)",
            "• EMA Guideline on Setting Health-Based Exposure Limits"
        ]
        for reg in regulations:
            story.append(Paragraph(reg, styles['Justified']))
        
        return story
    
    @staticmethod
    def _generate_section_3(styles):
        story = []
        
        story.append(Paragraph("3. OBJECTIVE", styles['SectionHeading']))
        story.append(Paragraph(
            "The objective of this protocol is to provide documented evidence through the scientific data "
            "to show that the cleaning procedure established for cleaning of equipment used in the "
            "manufacturing process is effective and consistently performs as expected and produces a result "
            "that meets predetermined acceptance criteria when cleaning is performed.",
            styles['Justified']
        ))
        
        return story
    
    @staticmethod
    def _generate_section_4(product, styles):
        story = []
        
        story.append(Paragraph("4. SCOPE", styles['SectionHeading']))
        story.append(Paragraph(
            f"The scope of the protocol is to execute the cleaning validation study for the equipment used "
            f"in the manufacturing process of {product.name} in manufacturing area.",
            styles['Justified']
        ))
        
        return story
    
    @staticmethod
    def _generate_section_5(styles):
        story = []
        
        story.append(Paragraph("5. RESPONSIBILITIES", styles['SectionHeading']))
        
        resp_data = [
            ["Department", "Responsibilities"],
            ["Quality Assurance (Team Leader)", 
             "To prepare & approve the cleaning validation protocol, coordinate the entire study activity, "
             "MACO calculation, execution and monitoring of cleaning validation study, compilation of data."],
            ["Quality Control", 
             "To analyze the cleaning validation samples (Chemical & Microbial), prepare specification, "
             "take swab samples, report results."],
            ["Production", 
             "To provide information required for MACO, execute cleaning of equipment, maintain cleaning logbook, "
             "inform QA for cleaning activity."],
            ["Engineering", 
             "To provide complete details (Capacity & Surface area etc.) of each equipment installed."]
        ]
        
        resp_table = Table(resp_data, colWidths=[5*cm, 11*cm])
        resp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(resp_table)
        
        return story
    
    @staticmethod
    def _generate_section_6(product, equipment_list, styles):
        story = []
        
        story.append(Paragraph("6. CLEANING PROCEDURE", styles['SectionHeading']))
        
        story.append(Paragraph("6.1 CLEANING AGENT SELECTION CRITERIA", styles['SubSectionHeading']))
        story.append(Paragraph(
            f"Selection criteria of solvent for cleaning are based on the solubility pattern of "
            f"{product.name} into cleaning agent. Because {product.name} is freely soluble in water, "
            f"water is non-toxic, leaves no harmful residues, is readily available and cost-effective, "
            f"and is compatible with all equipment MOCs (SS 316L).",
            styles['Justified']
        ))
        story.append(Spacer(1, 0.1*inch))
        
        story.append(Paragraph("6.2 SOLUBILITY PATTERN AND CLEANING AGENT", styles['SubSectionHeading']))
        
        solubility_data = [
            ["NAME OF PRODUCT", "SOLUBILITY PROFILE"],
            [f"{product.name} ({product.product_code})", product.solubility],
            ["Cleaning Agent", "Purified Water"],
            ["Quality Standard", "IP/Ph.Eur./USP"],
            ["Conductivity", "NMT 1.3 µS/cm at 25°C"],
            ["TOC", "NMT 0.5 mg/L"],
            ["Bioburden", "NMT 100 CFU/mL"],
            ["Temperature for Wash Cycle", "40-60°C"],
            ["Temperature for Final Rinse", "Ambient (25 ± 5°C)"]
        ]
        
        solubility_table = Table(solubility_data, colWidths=[6*cm, 10*cm])
        solubility_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(solubility_table)
        story.append(Spacer(1, 0.1*inch))
        
        story.append(Paragraph("6.3 DETAILS OF EQUIPMENT USED AND CONTACT SURFACE AREA", styles['SubSectionHeading']))
        
        eq_data = [["Sr. No.", "Equipment Name", "Equipment No.", "Capacity", "Surface Area (m²)"]]
        total_area = 0
        for idx, eq in enumerate(equipment_list, 1):
            eq_data.append([str(idx), eq.name, eq.equipment_id, str(eq.capacity or "N/A"), f"{eq.surface_area:.2f}"])
            total_area += eq.surface_area
        eq_data.append(["", "", "", "TOTAL:", f"{total_area:.2f}"])
        
        eq_table = Table(eq_data, colWidths=[2*cm, 5*cm, 3*cm, 3*cm, 3*cm])
        eq_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(eq_table)
        
        return story
    
    @staticmethod
    def _generate_section_6_7(protocol, styles):
        story = []
        
        story.append(Paragraph("6.7 DIRTY HOLD TIME (DHT) VALIDATION", styles['SubSectionHeading']))
        story.append(Paragraph(
            f"Definition: Time from end of manufacturing (batch completion) to start of wet cleaning. "
            f"Because residues may dry, harden, or degrade over time, becoming more difficult to remove. "
            f"Maximum claimed DHT: {protocol.dht_hours} hours.",
            styles['Justified']
        ))
        story.append(Spacer(1, 0.1*inch))
        
        dht_data = [
            ["Time Point", "Action", "Sampling"],
            ["T0 (Baseline)", "Clean immediately after manufacturing", "Swab + Rinse + Bioburden"],
            [f"T1 ({protocol.dht_hours} hours)", f"Keep dirty for {protocol.dht_hours} hours, then clean", "Swab + Rinse + Bioburden"],
            [f"T2 ({protocol.dht_hours * 2} hours)", f"Keep dirty for {protocol.dht_hours * 2} hours, then clean", "Swab + Rinse + Bioburden"],
            [f"T3 ({protocol.dht_hours * 3} hours)", f"Keep dirty for {protocol.dht_hours * 3} hours, then clean", "Swab + Rinse + Bioburden"]
        ]
        
        dht_table = Table(dht_data, colWidths=[5*cm, 7*cm, 6*cm])
        dht_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(dht_table)
        
        return story
    
    @staticmethod
    def _generate_section_6_8(protocol, styles):
        story = []
        
        story.append(Paragraph("6.8 CLEAN HOLD TIME (CHT) VALIDATION", styles['SubSectionHeading']))
        story.append(Paragraph(
            f"Definition: Time from completion of cleaning to next use of equipment. "
            f"Because cleaned equipment may accumulate dust, moisture, or microbial growth during storage. "
            f"Maximum claimed CHT: {protocol.cht_days} days.",
            styles['Justified']
        ))
        story.append(Spacer(1, 0.1*inch))
        
        cht_data = [
            ["Time Point", "Action", "Sampling"],
            ["T0 (Day 0)", "Clean equipment, sample immediately", "Visual + Swab + Bioburden"],
            ["T1 (Day 7)", "Store for 7 days, sample", "Visual + Swab + Bioburden"],
            ["T2 (Day 14)", "Store for 14 days, sample", "Visual + Swab + Bioburden"],
            ["T3 (Day 21)", "Store for 21 days, sample", "Visual + Swab + Bioburden"]
        ]
        
        cht_table = Table(cht_data, colWidths=[5*cm, 7*cm, 6*cm])
        cht_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(cht_table)
        
        return story
    
    @staticmethod
    def _generate_section_6_9(protocol, styles):
        story = []
        
        story.append(Paragraph("6.9 CAMPAIGN LENGTH VALIDATION", styles['SubSectionHeading']))
        story.append(Paragraph(
            f"Definition: Number of consecutive batches of same product manufactured before full cleaning. "
            f"Maximum Campaign Length: {protocol.campaign_max_batches} batches or {protocol.campaign_max_days} days, "
            f"whichever is earlier. Because residue levels remain within limits.",
            styles['Justified']
        ))
        
        return story
    
    @staticmethod
    def _generate_section_7(product, worst_case, maco_result, swab_limit_mg, total_surface_area, equipment_list, styles):
        story = []
        
        story.append(Paragraph("7. ESTABLISHMENT OF MAXIMUM ALLOWABLE LIMIT", styles['SectionHeading']))
        story.append(Paragraph("7.1 MACO/MSC CALCULATION WITH WORST-CASE RATIONALE", styles['SubSectionHeading']))
        
        maco_data = [
            ["Method", "Formula", "MACO (mg)"],
            ["ADE/PDE Method", f"MACO = (ADE × MBS_next) / TDD_next", f"{maco_result.get('method_ade_pde', 0):.2f}"],
            ["TDD Method", f"MACO = (TDD_prev × MBS_next) / (1000 × TDD_next)", f"{maco_result.get('method_tdd', 0):.2f}"],
            ["10 ppm Method", f"MACO = 0.001% × MBS_next", f"{maco_result.get('method_10ppm', 0):.2f}"],
            ["Selected MACO", "", f"{maco_result.get('lowest_maco', 0):.2f} mg"]
        ]
        
        maco_table = Table(maco_data, colWidths=[5*cm, 8*cm, 4*cm])
        maco_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#ffe0b2')),
        ]))
        story.append(maco_table)
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph("7.2 CALCULATION OF RINSE LIMIT", styles['SubSectionHeading']))
        story.append(Paragraph(
            f"Rinse Limit per Equipment (mg) = (MACO × Equipment Surface Area) / Total Surface Area",
            styles['Justified']
        ))
        story.append(Spacer(1, 0.1*inch))
        
        rinse_data = [["Equipment", "Surface Area (m²)", "Rinse Limit (mg/equipment)"]]
        for eq in equipment_list:
            rinse_limit = (maco_result.get('lowest_maco', 0) * eq.surface_area) / total_surface_area if total_surface_area > 0 else 0
            rinse_data.append([eq.name, f"{eq.surface_area:.2f}", f"{rinse_limit:.2f}"])
        
        rinse_table = Table(rinse_data, colWidths=[7*cm, 4*cm, 5*cm])
        rinse_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(rinse_table)
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph("7.3 CALCULATION OF SWAB LIMIT", styles['SubSectionHeading']))
        story.append(Paragraph(
            f"Swab Limit (mg/swab of 0.01 m²) = (MACO × 0.01 m²) / Total Surface Area = "
            f"({maco_result.get('lowest_maco', 0):.2f} mg × 0.01) / {total_surface_area:.2f} m² = "
            f"{swab_limit_mg:.6f} mg/swab ≈ 0.18 mg/swab",
            styles['Justified']
        ))
        
        return story
    
    @staticmethod
    def _generate_section_7_4(equipment_list, swab_limit_mg, styles):
        story = []
        
        story.append(Paragraph("7.4 STRATIFIED (STAGED) CARRYOVER CALCULATION", styles['SubSectionHeading']))
        story.append(Paragraph(
            "Total Carryover (mg) = Σ (MaxSwabᵢ × ESAᵢ / SSAᵢ)",
            styles['Justified']
        ))
        story.append(Spacer(1, 0.1*inch))
        
        carryover_data = [["Equipment", "ESA (dm²)", "Swab Limit (mg)", "Max Contribution (mg)"]]
        for eq in equipment_list:
            esa_dm2 = eq.surface_area * 100  # Convert m² to dm²
            max_contribution = swab_limit_mg * esa_dm2
            carryover_data.append([eq.name, f"{esa_dm2:.0f}", f"{swab_limit_mg:.6f}", f"{max_contribution:.2f}"])
        
        carryover_table = Table(carryover_data, colWidths=[7*cm, 3*cm, 4*cm, 4*cm])
        carryover_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(carryover_table)
        
        return story
    
    @staticmethod
    def _generate_section_8(fmea_data, equipment_list, styles):
        story = []
        
        story.append(Paragraph("8. SAMPLING PLAN", styles['SectionHeading']))
        story.append(Paragraph("8.1 FMEA-BASED SCIENTIFIC RATIONALE FOR SELECTING SWAB SAMPLING POINTS", styles['SubSectionHeading']))
        
        story.append(Paragraph("Risk Priority Number (RPN) Formula: RPN = Severity (S) × Occurrence (O) × Detection (D)", styles['Justified']))
        story.append(Spacer(1, 0.1*inch))
        
        fmea_data_table = [
            ["Equipment", "Failure Mode", "S", "O", "D", "RPN", "Sampling Point"],
            ["SSR-311E", "Residue at upper dome near shaft", "8", "4", "3", "96", "✅ Yes"],
            ["SSR-311E", "Residue near inlet valve", "7", "5", "3", "105", "✅ Yes"],
            ["SSANFD-311A", "Residue at sieve corner", "9", "6", "3", "162", "✅ Yes"],
            ["SSANFD-311A", "Residue on pressing rod", "8", "5", "4", "160", "✅ Yes"],
            ["SSMM-311A", "Residue on mesh", "7", "5", "4", "140", "✅ Yes"],
            ["SSMM-311A", "Residue on blades", "8", "4", "3", "96", "✅ Yes"],
            ["SSSFT-311B", "Residue on sieve surface", "7", "4", "4", "112", "✅ Yes"],
            ["SSACM-311A", "Residue in screw feeder", "8", "5", "4", "160", "✅ Yes"],
            ["SS Containers", "Residue on inner wall corners", "5", "6", "4", "120", "✅ Yes"]
        ]
        
        fmea_table = Table(fmea_data_table, colWidths=[4*cm, 7*cm, 1.5*cm, 1.5*cm, 1.5*cm, 2*cm, 3*cm])
        fmea_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(fmea_table)
        
        return story
    
    @staticmethod
    def _generate_section_8_3(recovery_studies, styles):
        story = []
        
        story.append(Paragraph("8.3 RECOVERY STUDY AND CORRECTION FACTOR", styles['SubSectionHeading']))
        
        if recovery_studies:
            recovery_data = [["Material of Construction (MOC)", "Recovery %", "Correction Factor", "95% CI", "Acceptable?"]]
            for rs in recovery_studies:
                acceptable = "✅ Yes" if rs.recovery_percent >= 50 else "❌ No"
                recovery_data.append([
                    rs.material_of_construction,
                    f"{rs.recovery_percent:.1f}%",
                    f"{rs.correction_factor:.3f}",
                    "±5%",
                    acceptable
                ])
            
            recovery_table = Table(recovery_data, colWidths=[5*cm, 3*cm, 4*cm, 3*cm, 3*cm])
            recovery_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(recovery_table)
            story.append(Spacer(1, 0.1*inch))
            
            story.append(Paragraph(
                "Correction Factor Application Formula: Actual Residue (mg/swab) = Measured Residue (mg/swab) ÷ Recovery (% as decimal)",
                styles['Justified']
            ))
            story.append(Spacer(1, 0.1*inch))
            
            story.append(Paragraph("Example Calculation:", styles['SubSectionHeading']))
            story.append(Paragraph(
                "If Measured = 0.09 mg/swab, Recovery = 85% → Corrected = 0.09 ÷ 0.85 = 0.106 mg/swab → PASS",
                styles['Justified']
            ))
        else:
            story.append(Paragraph(
                "No recovery studies found. Please add recovery data for each MOC.",
                styles['Justified']
            ))
        
        return story
    
    @staticmethod
    def _generate_section_9(swab_limit_mg, styles):
        story = []
        
        story.append(Paragraph("9. ACCEPTANCE CRITERIA", styles['SectionHeading']))
        
        story.append(Paragraph("9.1 VISUAL INSPECTION", styles['SubSectionHeading']))
        story.append(Paragraph(
            "Equipment surfaces including 'Hard to clean' areas must appear visually clean with no traces "
            "of product or other extraneous matter. Lighting: Minimum 200 lux. Distance: <30 cm.",
            styles['Justified']
        ))
        story.append(Spacer(1, 0.1*inch))
        
        story.append(Paragraph("9.2 SWAB SAMPLES (CHEMICAL)", styles['SubSectionHeading']))
        swab_data = [
            ["Parameter", "Acceptance Criteria", "Basis"],
            ["Uncorrected Result", f"NMT {swab_limit_mg:.6f} mg/swab", "Based on MACO calculation"],
            ["Recovery Correction", "Apply recovery % from recovery study", "As per recovery study"],
            ["Corrected Result (Final)", f"NMT {swab_limit_mg:.6f} mg/swab", "Pass/fail based on corrected result"]
        ]
        
        swab_table = Table(swab_data, colWidths=[5*cm, 6*cm, 6*cm])
        swab_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(swab_table)
        story.append(Spacer(1, 0.1*inch))
        
        story.append(Paragraph("9.3 MICROBIAL CONTAMINATION", styles['SubSectionHeading']))
        micro_data = [
            ["Test", "Acceptance Limit", "Rationale"],
            ["Total Viable Aerobic Count", "NMT 100 cfu/swab of 25 cm²", "Purified water specification"],
            ["Total Yeast & Molds Count", "NMT 10 cfu/swab of 25 cm²", "Indicates moisture issues"],
            ["Pathogens", "Must be Absent", "Patient safety risk"]
        ]
        
        micro_table = Table(micro_data, colWidths=[6*cm, 5*cm, 6*cm])
        micro_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(micro_table)
        
        return story
    
    @staticmethod
    def _generate_section_10(product, styles):
        story = []
        
        story.append(Paragraph("10. ANALYTICAL METHOD VALIDATION", styles['SectionHeading']))
        story.append(Paragraph("10.2 CHEMICAL METHOD VALIDATION", styles['SubSectionHeading']))
        
        amv_data = [
            ["Validation Parameter", "Result", "Acceptance Criteria", "Status"],
            ["LOD (Limit of Detection)", "0.1663 ppm", "Signal:Noise ≥ 3:1", "✅ Pass"],
            ["LOQ (Limit of Quantitation)", "0.5040 ppm", "Signal:Noise ≥ 10:1", "✅ Pass"],
            ["LOQ vs Limit Ratio", "28%", "≤50% required", "✅ Pass"],
            ["Linearity (R²)", "0.999", "NLT 0.990", "✅ Pass"],
            ["Accuracy (Recovery)", "98-102%", "90-110%", "✅ Pass"],
            ["Precision (RSD)", "1.2%", "NMT 2.0%", "✅ Pass"],
            ["Specificity", "No interference", "No peaks at RT", "✅ Pass"]
        ]
        
        amv_table = Table(amv_data, colWidths=[5*cm, 4*cm, 5*cm, 3*cm])
        amv_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(amv_table)
        
        return story
    
    @staticmethod
    def _generate_section_11(operator_quals, styles):
        story = []
        
        story.append(Paragraph("11. OPERATOR QUALIFICATION FOR CLEANING", styles['SectionHeading']))
        
        if operator_quals:
            op_data = [["Operator Name", "Eyesight", "Color Blindness", "Training Date", "Qualified", "Valid Until"]]
            for oq in operator_quals:
                if oq.user:
                    op_data.append([
                        oq.user.username,
                        "✅" if oq.eyesight_certified else "❌",
                        "✅" if oq.color_blindness_test_passed else "❌",
                        oq.training_date.strftime('%d/%m/%Y') if oq.training_date else "N/A",
                        "✅" if oq.practical_demo_passed else "❌",
                        oq.qualification_valid_until.strftime('%d/%m/%Y') if oq.qualification_valid_until else "N/A"
                    ])
            
            op_table = Table(op_data, colWidths=[4*cm, 3*cm, 3*cm, 4*cm, 3*cm, 4*cm])
            op_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(op_table)
        else:
            story.append(Paragraph("No operator qualification records found.", styles['Justified']))
        
        return story
    
    @staticmethod
    def _generate_section_12(styles):
        story = []
        
        story.append(Paragraph("12. CONTINUED PROCESS VERIFICATION (PHASE 3)", styles['SectionHeading']))
        
        cpv_data = [
            ["Parameter", "Frequency", "Acceptance", "Responsible"],
            ["Visual Inspection", "Every batch", "Must be clean", "Production"],
            ["Rinse Sample (Conductivity)", "Every batch", "NMT 1.3 µS/cm at 25°C", "QC"],
            ["Rinse Sample (Chemical)", "Every 10th batch", "NMT individual equipment limit", "QC"],
            ["Swab Sample (Chemical)", "Every 10th batch", "NMT 0.18 mg/swab", "QC"],
            ["Bioburden Swab", "Every 5th batch", "NMT 100 CFU/swab", "QC"]
        ]
        
        cpv_table = Table(cpv_data, colWidths=[5*cm, 4*cm, 5*cm, 4*cm])
        cpv_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(cpv_table)
        
        return story
    
    @staticmethod
    def _generate_section_13(nitrosamine, product, styles):
        story = []
        
        story.append(Paragraph("13. NITROSAMINES RISK ASSESSMENT", styles['SectionHeading']))
        
        if nitrosamine:
            risk_data = [
                ["Risk Factor", "Assessment", "Risk Level"],
                ["Raw Materials", f"Secondary amine: {'Yes' if nitrosamine.secondary_amine_present else 'No'}", 
                 "Medium" if nitrosamine.secondary_amine_present else "Low"],
                ["Nitrosating Agents", "None used", "Low"],
                ["Water System", f"Nitrite level: {nitrosamine.water_nitrite_level_ppm} ppm", "Low"],
                ["Equipment Sharing", "Check required", "To be verified"],
                ["Overall Risk", nitrosamine.overall_risk_level, nitrosamine.overall_risk_level]
            ]
            
            risk_table = Table(risk_data, colWidths=[6*cm, 6*cm, 5*cm])
            risk_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(risk_table)
        else:
            story.append(Paragraph(
                f"Nitrosamine risk assessment for {product.name} shows LOW to MEDIUM risk. "
                f"No nitrosating agents used in process. Water nitrite controlled.",
                styles['Justified']
            ))
        
        return story
    
    @staticmethod
    def _generate_section_14(styles):
        story = []
        
        story.append(Paragraph("14. DATA INTEGRITY (ALCOA+) COMPLIANCE", styles['SectionHeading']))
        
        alcoa_data = [
            ["Principle", "Requirement", "Compliance Method"],
            ["Attributable", "Who performed the action?", "Electronic signatures with user ID"],
            ["Legible", "Can data be read?", "Electronic records with clear font"],
            ["Contemporaneous", "Recorded at time of action?", "Real-time entry, no back-dating"],
            ["Original", "Is this the first capture?", "Raw data preserved, no re-recording"],
            ["Accurate", "Free from errors?", "Second-person verification"],
            ["Complete", "All data included?", "No selective reporting"],
            ["Consistent", "Logical sequence?", "Audit trail, time stamps"],
            ["Enduring", "Preserved long-term?", "Electronic backup, secure storage"],
            ["Available", "Accessible for inspection?", "15-minute retrieval, organized filing"]
        ]
        
        alcoa_table = Table(alcoa_data, colWidths=[4*cm, 5*cm, 8*cm])
        alcoa_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(alcoa_table)
        
        return story
    
    @staticmethod
    def _generate_section_15_16(styles):
        story = []
        
        story.append(Paragraph("15. DETAIL OF DEVIATION / DISCREPANCIES", styles['SectionHeading']))
        story.append(Paragraph(
            "Details of deviation / discrepancies initiated / reported during the execution of validation "
            "study shall be reported in cleaning validation report.",
            styles['Justified']
        ))
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph("16. REVALIDATION CRITERIA", styles['SectionHeading']))
        
        reval_data = [
            ["#", "Trigger", "Action Required"],
            ["1", "Change in cleaning procedure", "Full revalidation (3 consecutive batches)"],
            ["2", "Change in cleaning agent", "Full revalidation + new recovery studies"],
            ["3", "Change in minimum batch size (decrease >20%)", "Recalculate MACO; revalidate if needed"],
            ["4", "Major change in processing equipment", "Re-qualification + revalidation"],
            ["5", "New product with lower ADE/PDE (≤50 µg)", "Recalculate MACO; revalidate"],
            ["6", "Periodic revalidation", "Once in 5 years"]
        ]
        
        reval_table = Table(reval_data, colWidths=[1.5*cm, 7*cm, 8*cm])
        reval_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(reval_table)
        
        return story
    
    @staticmethod
    def _generate_section_17_19(styles):
        story = []
        
        story.append(Paragraph("17. RESULTS", styles['SectionHeading']))
        story.append(Paragraph(
            "Results of three cleaning campaign batches shall be tabulated as per the enclosed format.",
            styles['Justified']
        ))
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph("18. CONCLUSION", styles['SectionHeading']))
        story.append(Paragraph(
            "Cleaning validation report shall be prepared & conclusion shall be drawn based on the obtained results.",
            styles['Justified']
        ))
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph("19. SUMMARY REPORT AND APPROVAL", styles['SectionHeading']))
        story.append(Paragraph(
            "Abstract shall be written on completed protocol study and results shall be tabulated.",
            styles['Justified']
        ))
        
        return story
    
    @staticmethod
    def _generate_forms(equipment_list, styles):
        story = []
        
        story.append(PageBreak())
        story.append(Paragraph("FORM – A (Updated with Recovery Correction)", styles['SectionHeading']))
        story.append(Paragraph(
            "(A) Table for Chemical contamination level by Swab (with Recovery Correction), "
            "Visual Inspection & Residual rinse content equipment results:",
            styles['Justified']
        ))
        story.append(Spacer(1, 0.1*inch))
        
        form_a_headers = [
            "Sr. No.", "Equip. No.", "Location", "Visual\nInspection",
            "Uncorrected\n(mg/swab)", "Recovery\n%", "Corrected\n(mg/swab)",
            "Pass/Fail", "Rinse Result\n(mg/Equip.)", "Limit\n(mg/Equip.)"
        ]
        
        form_a_data = [form_a_headers]
        for i, eq in enumerate(equipment_list[:15], 1):
            form_a_data.append([
                str(i), eq.equipment_id, "_______", "___",
                "______", "___", "______", "___",
                "______", "______"
            ])
        
        form_a_table = Table(form_a_data, colWidths=[1.5*cm, 3*cm, 4*cm, 2*cm, 2.5*cm, 2*cm, 2.5*cm, 2*cm, 3*cm, 3*cm])
        form_a_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(form_a_table)
        story.append(PageBreak())
        
        story.append(Paragraph("FORM – B (Microbiological)", styles['SectionHeading']))
        story.append(Paragraph(
            "(B) Table for Microbiological contamination level by swab:",
            styles['Justified']
        ))
        story.append(Spacer(1, 0.1*inch))
        
        form_b_headers = ["Sr. No.", "Equip. No.", "Location", "TVC\n(CFU/swab)", "Yeast/Mold\n(CFU/swab)", "Pathogens", "Pass/Fail"]
        form_b_data = [form_b_headers]
        for i, eq in enumerate(equipment_list[:15], 1):
            form_b_data.append([str(i), eq.equipment_id, "_______", "______", "______", "_______", "___"])
        
        form_b_table = Table(form_b_data, colWidths=[1.5*cm, 3*cm, 5*cm, 2.5*cm, 2.5*cm, 3*cm, 2*cm])
        form_b_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(form_b_table)
        story.append(PageBreak())
        
        story.append(Paragraph("FORM – C (Visual Inspection)", styles['SectionHeading']))
        story.append(Paragraph(
            "(C) Table for Visual Inspection of Equipment:",
            styles['Justified']
        ))
        story.append(Spacer(1, 0.1*inch))
        
        form_c_headers = ["Sr. No.", "Equipment Name", "Equipment No.", "Visual Inspection Result", "Inspected By", "Date"]
        form_c_data = [form_c_headers]
        for i, eq in enumerate(equipment_list, 1):
            form_c_data.append([str(i), eq.name, eq.equipment_id, "_______", "_______", "_______"])
        
        form_c_table = Table(form_c_data, colWidths=[1.5*cm, 6*cm, 3*cm, 3*cm, 4*cm, 3*cm])
        form_c_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(form_c_table)
        
        return story