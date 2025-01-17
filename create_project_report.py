import argparse
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from datetime import datetime
from reportlab.lib.colors import HexColor
import re


def draw_detail_page(c, title, details, page_number):
    """Helper function to draw detail pages"""
    width, height = letter
    
    # Add a back button
    c.setFont("Helvetica", 12)  # Changed to regular weight
    c.setFillColor(HexColor('#0000FF'))
    c.linkRect("< Back", "page1", 
               (30, height - 40, 80, height - 20), 
               relative=0)
    c.drawString(30, height - 35, "< Back")
    
    # Draw the title
    c.setFont("Helvetica-Bold", 20)  # Reduced font size slightly
    c.setFillColor(colors.black)
    title_width = c.stringWidth(title, "Helvetica-Bold", 20)
    c.drawString((width - title_width) / 2, height - 50, title)
    
    if title == "Benchmarking Details":
        # Parse JSON string to dict
        import json
        try:
            data = json.loads(''.join(details))
            
            # Table settings
            table_width = 400
            row_height = 25  # Slightly reduced row height
            col_width = table_width / 2
            margin = (width - table_width) / 2  # Center the table
            
            # Calculate table dimensions
            table_height = len(data) * row_height
            
            # Start position for the table (centered)
            start_x = margin
            start_y = height - 150  # Start below the title
            
            # Draw outer table border
            c.setStrokeColor(colors.black)
            c.setLineWidth(1)  # Thinner border
            c.rect(start_x, start_y - table_height, table_width, table_height)
            
            # Draw horizontal lines
            c.setLineWidth(0.5)  # Thinner lines
            y = start_y
            for i in range(len(data) + 1):
                c.line(start_x, y - row_height, start_x + table_width, y - row_height)
                y -= row_height

            # Draw vertical line for columns
            c.line(start_x + col_width, start_y - table_height, start_x + col_width, start_y)

            # Add text
            text_padding = 10
            y = start_y - row_height + 10
            
            # Add table content
            c.setFont("Helvetica", 10)  # Smaller, regular font
            for key, value in data.items():
                c.drawString(start_x + text_padding, y, str(key))
                c.drawString(start_x + col_width + text_padding, y, str(value))
                y -= row_height
                
        except json.JSONDecodeError:
            # Fallback to original text display if JSON parsing fails
            y = height - 100
            c.setFont("Helvetica", 10)  # Consistent font size
            for detail in details:
                if y < 50:
                    c.showPage()
                    y = height - 50
                c.drawString(50, y, detail.strip())
                y -= 20
    else:
        # Original text display for other pages
        y = height - 100
        c.setFont("Helvetica", 10)  # Consistent font size
        for detail in details:
            if y < 50:
                c.showPage()
                y = height - 50
            c.drawString(50, y, detail.strip())
            y -= 20

def extract_test_results(testing_log):
    # Open the testing log file and read its content
    with open(testing_log, 'r') as f:
        log_content = f.read()

    # Look for the line that contains test results, like: "Ran 4 tests in 0.006s"
    match = re.search(r'Ran (\d+) tests? in.*\s*(OK|FAILED)', log_content)
    
    if match:
        total_tests = int(match.group(1))  # Extract total tests
        result = match.group(2)  # Extract the result (OK or FAILED)
        
        # If the result is 'OK', we assume all tests passed
        if result == 'OK':
            passed_tests = total_tests
            return f"OK {passed_tests}/{total_tests}"
        else:
            # If the result is 'FAILED', we consider it as 'NOT OK'
            return f"NOT OK {passed_tests}/{total_tests}"
    else:
        return "NOT OK 0/0"  # In case the log format is unexpected or empty


def extract_test_results(testing_log):
    # Open the testing log file and read its content
    with open(testing_log, 'r') as f:
        log_content = f.read()

    # Look for the line that contains test results, like: "Ran 4 tests in 0.006s"
    match = re.search(r'Ran (\d+) tests? in.*\s*(OK|FAILED)', log_content)
    
    if match:
        total_tests = int(match.group(1))  # Extract total tests
        result = match.group(2)  # Extract the result (OK or FAILED)
        
        # If the result is 'OK', we assume all tests passed
        if result == 'OK':
            passed_tests = total_tests
            return f"OK {passed_tests}/{total_tests}"
        else:
            # If the result is 'FAILED', we consider it as 'NOT OK'
            return f"NOT OK {passed_tests}/{total_tests}"
    else:
        return "NOT OK 0/0"  # In case the log format is unexpected or empty

def generate_pdf(benchmarking_done, testing_done, deprecated_check_done, sonar_analysis_done, admin_email, benchmarking_log, testing_log, deprecated_check_log, sonar_analysis_log):
    pdf_filename = '/tmp/report.pdf'
    c = canvas.Canvas(pdf_filename, pagesize=letter)
    width, height = letter

    # Create navigation destinations
    c.bookmarkPage('page1')
    
    # Title
    c.setFont("Helvetica-Bold", 30)
    title = "Automated Build Report"
    title_width = c.stringWidth(title, "Helvetica-Bold", 30)
    c.drawString((width - title_width) / 2, height - 50, title)

    # Table settings
    table_width = 500
    row_height = 40
    col_width = table_width / 2
    margin = 50
    
    # Extract testing result in the format "OK 4/4"
    test_result = extract_test_results(testing_log)

    # Replace True/False with "OK"/"NOT OK"
    data = [
        ["Parameter", "Status"],
        ["Benchmarking", "OK" if benchmarking_done == 'true' else "NOT OK"],
        ["Testing", test_result],  # Display test result here
        ["Deprecated Check", "OK" if deprecated_check_done == 'true' else "NOT OK"],
        ["Sonar Analysis", "OK" if sonar_analysis_done == 'true' else "NOT OK"]
    ]
    
    # Calculate table dimensions
    table_height = len(data) * row_height
    
    # Center the table on the page
    start_x = margin
    start_y = height - ((height - table_height) / 2)
    
    # Draw outer table border
    c.setStrokeColor(colors.black)
    c.setLineWidth(2)
    c.rect(start_x, start_y - table_height, table_width, table_height)
    
    # Draw header row with different background
    c.setFillColor(colors.lightgrey)
    c.rect(start_x, start_y - row_height, table_width, row_height, fill=1, stroke=0)
    c.setFillColor(colors.black)

    # Draw horizontal lines
    c.setLineWidth(1)
    y = start_y
    for i in range(len(data) + 1):
        c.line(start_x, y - row_height, start_x + table_width, y - row_height)
        y -= row_height

    # Draw vertical line for columns
    c.line(start_x + col_width, start_y - table_height, start_x + col_width, start_y)

    # Add text with clickable links
    text_padding = 10
    y = start_y - row_height + 15
    
    page_number = 2
    for row in data:
        if row[0] != "Parameter":  # Don't make header clickable
            # Make the text blue to indicate it's clickable
            c.setFillColor(HexColor('#0000FF'))
            # Create clickable area with proper coordinates list
            rect = (start_x + text_padding, y - 10, 
                   start_x + col_width, y + 10)
            c.linkRect(row[0], f'page{page_number}', rect, relative=0)
            page_number += 1
            
        # Draw the text
        c.setFont("Helvetica-Bold" if y == start_y - row_height + 15 else "Helvetica", 12)
        c.drawString(start_x + text_padding, y, str(row[0]))
        
        # Status column
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold" if y == start_y - row_height + 15 else "Helvetica", 12)
        c.drawString(start_x + col_width + text_padding, y, str(row[1]))
        
        y -= row_height

    # Add detail pages with log content
    # Benchmarking Details
    c.showPage()
    c.bookmarkPage('page2')
    with open(benchmarking_log, 'r') as f:
        benchmarking_details = f.readlines()
    draw_detail_page(c, "Benchmarking Details", benchmarking_details, 2)

    # Testing Details
    c.showPage()
    c.bookmarkPage('page3')
    with open(testing_log, 'r') as f:
        testing_details = f.readlines()
    draw_detail_page(c, "Testing Details", testing_details, 3)

    # Deprecated Check Details
    c.showPage()
    c.bookmarkPage('page4')
    with open(deprecated_check_log, 'r') as f:
        deprecated_check_details = f.readlines()
    draw_detail_page(c, "Deprecated Check Details", deprecated_check_details, 4)

    # Sonar Analysis Details
    c.showPage()
    c.bookmarkPage('page5')
    with open(sonar_analysis_log, 'r') as f:
        sonar_analysis_details = f.readlines()
    draw_detail_page(c, "Sonar Analysis Details", sonar_analysis_details, 5)

    c.save()
    return pdf_filename



def send_email(pdf_filename, admin_email):
    sender_email = "technowebofficial01@gmail.com"
    receiver_email = admin_email
    password = "qcazcbycugzclhpt"

    subject = "Automated Build Report"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    with open(pdf_filename, "rb") as pdf_file:
        attach_part = MIMEBase('application', 'octet-stream')
        attach_part.set_payload(pdf_file.read())
        encoders.encode_base64(attach_part)
        attach_part.add_header('Content-Disposition', 'attachment', filename="report.pdf")
        msg.attach(attach_part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email. Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Generate a report and send it via email.")
    parser.add_argument('benchmarking_done', type=str, help="Benchmarking status")
    parser.add_argument('testing_done', type=str, help="Testing status")
    parser.add_argument('deprecated_check_done', type=str, help="Deprecated libraries check status")
    parser.add_argument('sonar_analysis_done', type=str, help="Sonar analysis status")
    parser.add_argument('admin_email', type=str, help="Admin email address to send the report")
    parser.add_argument('benchmarking_log', type=str, help="Path to benchmarking log file")
    parser.add_argument('testing_log', type=str, help="Path to testing log file")
    parser.add_argument('deprecated_check_log', type=str, help="Path to deprecated check log file")
    parser.add_argument('sonar_analysis_log', type=str, help="Path to sonar analysis log file")

    args = parser.parse_args()

    pdf_filename = generate_pdf(args.benchmarking_done, args.testing_done, args.deprecated_check_done, args.sonar_analysis_done, args.admin_email, args.benchmarking_log, args.testing_log, args.deprecated_check_log, args.sonar_analysis_log)
    send_email(pdf_filename, args.admin_email)

if __name__ == "__main__":
    main()
