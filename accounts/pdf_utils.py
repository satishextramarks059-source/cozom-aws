from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from datetime import datetime
from .models import HospitalDoctors


class AppointmentPDFGenerator:
    def __init__(self, appointment):
        self.appointment = appointment
        self.patient = appointment.patient
        self.doctor = appointment.doctor
        self.hospital = appointment.hospital
        self.user = self.patient.user
        # Handle both doctor and hospital bookings
        self.doctor_user = self.doctor.user if self.doctor else None
        self.is_doctor_booking = self.doctor is not None
        self.is_hospital_booking = self.hospital is not None

    def generate(self):
        """Generate PDF and return BytesIO object"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Add custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#0d6efd'),
            spaceAfter=30,
            alignment=1  # center
        )
        
        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#0d6efd'),
            spaceAfter=10,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        )
        
        label_style = ParagraphStyle(
            'Label',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            fontName='Helvetica-Bold'
        )
        
        value_style = ParagraphStyle(
            'Value',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333')
        )
        
        # Header
        elements.append(Paragraph("Appointment", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Patient and Doctor Details (Two columns)
        patient_data = [
            [Paragraph("Patient Details", section_style)],
            [Paragraph(f"<b>Full Name:</b> {self.patient.full_name}", value_style)],
            [Paragraph(f"<b>Phone:</b> {self.user.phone_number}", value_style)],
            [Paragraph(f"<b>Email:</b> {self.user.email}", value_style)],
            [Paragraph(f"<b>Address:</b> {self.patient.address}", value_style)],
            [Paragraph(f"<b>Message:</b> {self.appointment.patient_message or 'N/A'}", value_style)],
        ]
        
        # Build doctor or hospital details based on booking type
        if self.is_doctor_booking:
            specialization = ", ".join([s.name for s in self.doctor.specializations.all()]) or "N/A"
            
            # Get hospital if doctor is associated with one
            hospital_doctor = HospitalDoctors.objects.filter(doctor=self.doctor, is_active=True).first()
            hospital_name = hospital_doctor.hospital.name if hospital_doctor else "N/A"
            
            provider_data = [
                [Paragraph("Doctor Details", section_style)],
                [Paragraph(f"<b>Full Name:</b> {self.doctor.doctor_name}", value_style)],
                [Paragraph(f"<b>Specialization:</b> {specialization}", value_style)],
                [Paragraph(f"<b>Phone:</b> {self.doctor_user.phone_number}", value_style)],
                [Paragraph(f"<b>Email:</b> {self.doctor_user.email}", value_style)],
                [Paragraph(f"<b>Address:</b> {self.doctor.address or 'N/A'}", value_style)],
                [Paragraph(f"<b>State:</b> {self.doctor.state or 'N/A'}", value_style)],
                [Paragraph(f"<b>City:</b> {self.doctor.city or 'N/A'}", value_style)],
                [Paragraph(f"<b>Hospital Name:</b> {hospital_name}", value_style)],
            ]
        else:  # Hospital booking
            provider_data = [
                [Paragraph("Hospital Details", section_style)],
                [Paragraph(f"<b>Hospital Name:</b> {self.hospital.name}", value_style)],
                [Paragraph(f"<b>Phone:</b> {self.hospital.user.phone_number}", value_style)],
                [Paragraph(f"<b>Email:</b> {self.hospital.user.email}", value_style)],
                [Paragraph(f"<b>Address:</b> {self.hospital.address or 'N/A'}", value_style)],
                [Paragraph(f"<b>State:</b> {self.hospital.state or 'N/A'}", value_style)],
                [Paragraph(f"<b>City:</b> {self.hospital.city or 'N/A'}", value_style)],
                [Paragraph(f"<b>Country:</b> {self.hospital.country or 'N/A'}", value_style)],
                [Paragraph(f"<b>24x7 Emergency:</b> {'Yes' if self.hospital.emergency_services else 'No'}", value_style)],
            ]
        
        # Create two-column layout for details
        details_table = Table(
            [[Table([[cell] for cell in patient_data], colWidths=[3*inch]), 
              Table([[cell] for cell in provider_data], colWidths=[3*inch])]],
            colWidths=[3.25*inch, 3.25*inch]
        )
        details_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(details_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Appointment Timing Section
        time_label = "Time Given by Doctor:" if self.is_doctor_booking else "Appointment Time:"
        timing_data = [
            [
                Paragraph(f"<b>Appointment Date:</b><br/>{self.appointment.appointment_date.strftime('%B %d, %Y')}", value_style),
                Paragraph(f"<b>{time_label}</b><br/>{self.appointment.doctor_provided_time.strftime('%I:%M %p') if self.appointment.doctor_provided_time else 'N/A'}", value_style)
            ]
        ]
        
        timing_table = Table(timing_data, colWidths=[3.25*inch, 3.25*inch])
        timing_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ]))
        elements.append(timing_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Payment Status Section
        elements.append(Paragraph("Payment Status", section_style))
        payment_location = "Doctor's Place" if self.is_doctor_booking else "Hospital's Place"
        payment_data = [
            [Paragraph("Paid via COZOM portal?", value_style), Paragraph("☐ Yes", value_style), Paragraph("☐ No", value_style)],
            [Paragraph(f"Patient Paid at {payment_location}?", value_style), Paragraph("☐ Yes", value_style), Paragraph("☐ No", value_style)],
        ]
        
        payment_table = Table(payment_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        payment_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(payment_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Signature Section
        elements.append(Paragraph("Signature Section", section_style))
        signature_label = "Doctor Sign / Assistance Sign" if self.is_doctor_booking else "Hospital Authority Sign"
        signature_data = [
            [
                Paragraph("<b>Patient Sign</b><br/><br/><br/>", value_style),
                Paragraph(f"<b>{signature_label}</b><br/><br/><br/>", value_style)
            ]
        ]
        
        signature_table = Table(signature_data, colWidths=[3.25*inch, 3.25*inch])
        signature_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(signature_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Important Note Section
        note_style = ParagraphStyle(
            'Note',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor("#EFBB3A"),
            alignment=0  # left
        )
        elements.append(Paragraph("<b>Important Note:</b> Please present this appointment confirmation at the reception desk to verify your arrival and confirm your appointment.", note_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            alignment=1  # center
        )
        elements.append(Paragraph("Thank you for choosing COZOM, we care about your health.", footer_style))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer


def generate_appointment_pdf(appointment):
    """
    Helper function to generate appointment PDF
    Returns BytesIO object containing the PDF
    """
    generator = AppointmentPDFGenerator(appointment)
    return generator.generate()
