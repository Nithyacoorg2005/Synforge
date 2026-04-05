from fpdf import FPDF
import datetime
import os

class SynForgeReporter:
    def __init__(self, job_id, metrics):
        self.job_id = job_id
        self.metrics = metrics
        self.pdf = FPDF()

    def generate_report(self):
        self.pdf.add_page()
        
        # 1. Header & Branding
        self.pdf.set_font("Arial", 'B', 16)
        self.pdf.cell(200, 10, txt="SynForge: Privacy Audit Certificate", ln=True, align='C')
        self.pdf.set_font("Arial", size=10)
        self.pdf.cell(200, 10, txt=f"Report ID: {self.job_id}", ln=True, align='C')
        self.pdf.cell(200, 10, txt=f"Verification Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
        self.pdf.ln(10)

        # 2. Executive Summary
        self.pdf.set_font("Arial", 'B', 12)
        self.pdf.cell(200, 10, txt="1. Executive Summary", ln=True)
        self.pdf.set_font("Arial", size=11)
        self.pdf.multi_cell(0, 10, txt="This document verifies that the synthetic dataset has undergone adversarial privacy testing and statistical fidelity benchmarking. SynForge utilizes Differential Privacy (DP) to mitigate re-identification risks.")
        self.pdf.ln(5)

        # 3. Core Privacy & Fidelity Metrics
        self.pdf.set_fill_color(240, 240, 240)
        self.pdf.set_font("Arial", 'B', 11)
        self.pdf.cell(95, 10, "Security Metric", 1, 0, 'C', True)
        self.pdf.cell(95, 10, "Score / Value", 1, 1, 'C', True)
        
        self.pdf.set_font("Arial", size=11)
        self.pdf.cell(95, 10, "Statistical Fidelity", 1)
        self.pdf.cell(95, 10, f"{self.metrics.get('fidelity', 0)*100:.1f}%", 1, 1, 'C')
        
        self.pdf.cell(95, 10, "Privacy Risk Score (MIA)", 1)
        self.pdf.cell(95, 10, f"{self.metrics.get('privacy_risk', 'N/A')}", 1, 1, 'C')
        
        self.pdf.cell(95, 10, "DP Privacy Budget (Epsilon)", 1)
        self.pdf.cell(95, 10, f"{self.metrics.get('epsilon', 'N/A')}", 1, 1, 'C')
        self.pdf.ln(10)

        # 4. NEW: Machine Learning Utility (TSTR) Section
        tstr_data = self.metrics.get('tstr_results', {})
        if tstr_data:
            self.pdf.set_font("Arial", 'B', 12)
            self.pdf.cell(200, 10, txt="2. Machine Learning Utility (TSTR)", ln=True)
            self.pdf.set_font("Arial", size=11)
            self.pdf.multi_cell(0, 10, txt="Train on Synthetic, Test on Real (TSTR) evaluates if a model trained on this dataset maintains predictive power on real-world data.")
            
            self.pdf.cell(95, 10, "TSTR Accuracy", 1)
            self.pdf.cell(95, 10, f"{tstr_data.get('tstr_score', 0)*100:.1f}%", 1, 1, 'C')
            
            self.pdf.cell(95, 10, "Utility Gap (Real vs Syn)", 1)
            gap = tstr_data.get('utility_gap', 0)
            self.pdf.cell(95, 10, f"{gap*100:.1f}%", 1, 1, 'C')
            self.pdf.ln(10)

        # 5. Critical Privacy Alert (Triggered if Risk >= 0.8)
        if self.metrics.get('privacy_risk', 0) >= 0.8:
            self.pdf.set_fill_color(255, 230, 230) # Light Red
            self.pdf.set_text_color(180, 0, 0)      # Deep Red
            self.pdf.set_font("Arial", 'B', 11)
            self.pdf.cell(190, 10, "CRITICAL PRIVACY ALERT", 1, 1, 'C', True)
            self.pdf.set_font("Arial", size=10)
            self.pdf.multi_cell(0, 8, txt="Dataset vulnerability detected. Re-identification risk (MIA) exceeds safety thresholds. RECOMMENDATION: Lower Epsilon (epsilon < 0.5) and re-synthesize.", border=1)
            self.pdf.ln(5)
            self.pdf.set_text_color(0, 0, 0) # Reset to Black

        # 6. Legal Disclaimer
        self.pdf.set_font("Arial", 'I', 8)
        self.pdf.set_text_color(100, 100, 100)
        self.pdf.multi_cell(0, 5, txt="Disclaimer: This report is based on automated adversarial simulations. Scores represent estimates of statistical similarity and membership inference resistance. While SynForge utilizes DP-GAN architectures, users should verify compliance with specific local regulations (GDPR/HIPAA).")

        # Ensure directory exists and save
        output_path = f"data/reports/audit_{self.job_id}.pdf"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self.pdf.output(output_path)
        return output_path