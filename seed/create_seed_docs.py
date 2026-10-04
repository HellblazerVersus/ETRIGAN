import pymupdf as fitz
from pathlib import Path

SEED_DIR = Path(__file__).resolve().parent
SEED_DIR.mkdir(parents=True, exist_ok=True)

def create_piping_sop_pdf():
    doc = fitz.open()
    
    # Page 1
    page1 = doc.new_page()
    text1 = """MANGALORE REFINERY AND PETROCHEMICALS LIMITED (ACME)
STANDARD OPERATING PROCEDURE: SOP-CDU-042
Revision: 04 | Effective Date: 15-Jan-2024
Subject: Crude Distillation Unit (CDU) Overhead Piping Inspection & Integrity

1. PURPOSE & SCOPE
This document defines mandatory inspection intervals, ultrasonic thickness gauging protocols, and retirement thickness criteria for crude overhead condensing line 12-CDU-0104 and associated spools.

2. CORROSION MECHANISMS
The overhead vapor line experiences aggressive dew-point hydrochloric acid (HCl) corrosion and ammonium chloride (NH4Cl) fouling at temperatures between 95°C and 130°C. Neutralizing amine injection (NA-102) must be continuously maintained at 12 ppm.

3. INSPECTION FREQUENCY
In accordance with API 570 Class 1 Service:
- Full external visual inspection: Every 6 months.
- Ultrasonic thickness (UT) scanning: Every 12 months at designated Condition Monitoring Locations (CML 01 through CML 12).
"""
    rect1 = fitz.Rect(50, 50, 550, 750)
    page1.insert_textbox(rect1, text1, fontsize=11)

    # Page 2
    page2 = doc.new_page()
    text2 = """ACME STANDARD SOP-CDU-042 (Page 2)

4. RETIREMENT THICKNESS CRITERIA (T_min)
Design Pressure (P): 14.8 kg/cm2g
Design Temperature (T): 135°C
Material: ASTM A106 Grade B Carbon Steel (Nominal Thickness: 7.11 mm)
Allowable Stress (S): 1200 kg/cm2
Joint Efficiency (E): 1.0

The minimum structural retirement thickness (T_min) is calculated per ASME B31.3 Section 304.1.2:
T_min = (P * D) / (2 * (S * E + P * 0.4)) + Corrosion Allowance
Calculated T_min for line 12-CDU-0104 = 3.42 mm.

5. ACTION LEVELS & APPROVAL PROTOCOL
- Reading > 4.5 mm: Satisfactory, continue standard 12-month interval.
- Reading 3.5 mm to 4.5 mm: Flag for quarterly re-inspection; schedule replacement spool.
- Reading < 3.42 mm: CRITICAL RETIREMENT. Immediate derating or turnaround replacement approval note must be generated for sign-off by Chief General Manager (Inspection).
"""
    rect2 = fitz.Rect(50, 50, 550, 750)
    page2.insert_textbox(rect2, text2, fontsize=11)

    pdf_path = SEED_DIR / "ACME_SOP_CDU_042_Crude_Overhead_Piping.pdf"
    doc.save(str(pdf_path))
    print(f"Created: {pdf_path}")

def create_hot_work_pdf():
    doc = fitz.open()
    page1 = doc.new_page()
    text1 = """MANGALORE REFINERY AND PETROCHEMICALS LIMITED (ACME)
FIRE & SAFETY MANUAL: RULE FSM-202
Subject: Hot Work Permitting Protocol for Hydrocarbon Processing Units

1. MANDATORY CLEARANCES BEFORE HOT WORK
No cutting, welding, grinding, or open-flame work may commence within battery limits without a valid Class A Hot Work Permit signed by Plant Safety Superintendent.

2. MANDATORY CHECKLIST
- Lower Explosive Limit (LEL) testing: Must read 0.0% LEL. Any reading > 1% strictly halts work.
- Flange positive isolation: Mechanical slip blinding at all battery limit flanges (BL-01 to BL-08).
- Fire protection: Continuous pressurized fire water hose with fog nozzle manned at the work site.
- Spark containment: Fire-retardant tarpaulin enclosure around welding zone.
"""
    rect_hw = fitz.Rect(50, 50, 550, 750)
    page1.insert_textbox(rect_hw, text1, fontsize=11)
    pdf_path = SEED_DIR / "ACME_FSM_202_Hot_Work_Permits.pdf"
    doc.save(str(pdf_path))
    print(f"Created: {pdf_path}")

if __name__ == "__main__":
    create_piping_sop_pdf()
    create_hot_work_pdf()
