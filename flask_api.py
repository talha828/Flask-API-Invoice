import os

import uvicorn
from flask import Flask, request, jsonify, send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)

def create_invoice_data(customer_data, company_name="Yousaf Meo", date="August - 2024", milk_price_per_liter=220):
    invoice_list = []

    for data in customer_data:
        # Split the data into parts
        name, milk_data, previous_balance = data.split(':')

        # Extract milk details from brackets
        milk_entries = milk_data.strip('()').split(')(')
        items = []
        total_milk = 0
        total_days = 0

        for entry in milk_entries:
            milk_qty, day_count = map(float, entry.split('-'))
            total_milk += milk_qty * day_count
            total_days += day_count

            items.append({
                "description": f"{day_count} Days",
                "amount": milk_qty,
                "Price": (milk_qty * milk_price_per_liter) * day_count
            })

        # Calculate totals
        total_monthly_amount = sum(item['Price'] for item in items)
        previous_balance = float(previous_balance)
        total_amount = total_monthly_amount + previous_balance

        # Create the invoice dictionary
        invoice_data = {
            "company_name": company_name,
            "client_name": name,
            "items": items,
            "total_monthly_amount": round(total_monthly_amount, 2),
            "total_amount": round(total_amount, 2),
            "total_days": f"{total_days} Days",
            "previous_balance": round(previous_balance, 2),
            "total_milk": f"{total_milk:.2f}(L)",
            "date": date,
        }

        invoice_list.append(invoice_data)

    return invoice_list

def create_invoice(invoice_data_list):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Set up grid dimensions for the 3x3 matrix
    rows = 5
    cols = 3
    invoice_width = width / cols
    invoice_height = height / rows

    # To store customer names and their total amounts for the summary page
    customer_summaries = []
    grand_total = 0

    # Loop through each invoice and position it within the grid
    for i, invoice_data in enumerate(invoice_data_list):
        # Calculate the row and column position
        col = i % cols
        row = (i // cols) % rows
        page_number = i // (rows * cols)

        if i != 0 and i % (rows * cols) == 0:
            c.showPage()  # Start a new page for the next set of invoices

        x_position = col * invoice_width + 20
        y_position = height - (row + 1) * invoice_height + invoice_height - 20

        # Extract invoice details
        company_name = invoice_data['company_name']
        client_name = invoice_data['client_name']
        items = invoice_data['items']
        total_amount = invoice_data['total_amount']
        total_monthly_amount = invoice_data['total_monthly_amount']
        previous_balance = invoice_data['previous_balance']
        total_days = invoice_data['total_days']
        total_milk = invoice_data['total_milk']
        date = invoice_data['date']
        long_line = "__________________________________________"

        # Add company name and client name
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x_position, y_position, f"{client_name}")

        # Add invoice heading
        c.setFont("Helvetica", 8)
        c.drawString(x_position, y_position - 12, company_name)

        # Add invoice date
        c.setFont("Helvetica", 7)
        c.drawString(x_position, y_position - 24, date)

        # Add the table headers
        c.setFont("Helvetica", 7)
        c.drawString(x_position, y_position - 36, "Days-No")
        c.drawString(x_position + 50, y_position - 36, "Milk L")
        c.drawString(x_position + 100, y_position - 36, "Amount L")

        c.drawString(x_position, y_position - 38, long_line)

        # Add invoice items
        y_item_position = y_position - 50
        for item in items:
            description, amount, price = item['description'], item['amount'], item['Price']
            c.drawString(x_position, y_item_position, description)
            c.drawString(x_position + 50, y_item_position, f"{amount}")
            c.drawString(x_position + 100, y_item_position, f"Rs.{price}")
            y_item_position -= 10  # Move to the next line

        c.drawString(x_position, y_item_position + 8, long_line)

        # Draw totals
        c.drawString(x_position, y_item_position - 5, total_days)
        c.drawString(x_position + 50, y_item_position - 5, total_milk)
        c.drawString(x_position + 100, y_item_position - 5, f"{int(total_monthly_amount)}")

        c.drawString(x_position, y_item_position - 15, "Previous Balance")
        c.drawString(x_position + 100, y_item_position - 15, f"{int(previous_balance)}")

        c.drawString(x_position, y_item_position - 25, long_line)

        c.setFont("Helvetica-Bold", 9)
        c.drawString(x_position, y_item_position - 40, "Total Balance")
        c.drawString(x_position + 100, y_item_position - 40, f"{int(total_amount)}")

        # Add customer name and total amount to the summary list
        customer_summaries.append((client_name, total_amount))
        grand_total += total_amount

    # Add the summary page at the end
    c.showPage()
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, height - 50, "Customer Summary")

    # Divide the summary into two columns
    left_column_customers = customer_summaries[:len(customer_summaries) // 2]
    right_column_customers = customer_summaries[len(customer_summaries) // 2:]

    # Set initial positions for the columns
    x_left_column = 30
    x_right_column = width / 2 + 30
    y_summary_position = height - 80
    line_height = 20

    c.setFont("Helvetica", 10)

    # Print left column
    for client_name, total_amount in left_column_customers:
        c.drawString(x_left_column, y_summary_position, f"{client_name}: Rs.{int(total_amount)}")
        y_summary_position -= line_height  # Move to the next line

    # Reset y position for the right column
    y_summary_position = height - 80

    # Print right column
    for client_name, total_amount in right_column_customers:
        c.drawString(x_right_column, y_summary_position, f"{client_name}: Rs.{int(total_amount)}")
        y_summary_position -= line_height  # Move to the next line

    # Print the grand total at the bottom of the page
    y_summary_position -= 2 * line_height  # Add extra space before the grand total
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_left_column, y_summary_position, f"Grand Total: Rs.{int(grand_total)}")

    # Save the PDF
    c.save()
    buffer.seek(0)
    return buffer


@app.route('/generate-invoice', methods=['POST'])
def generate_invoice():
    data = request.json
    customer_data = data.get('customer_data')
    date = data.get('date', "August - 2024")
    milk_price_per_liter = data.get('milk_price_per_liter', 220)

    invoice_data_list = create_invoice_data(customer_data, date=date, milk_price_per_liter=milk_price_per_liter)
    pdf_buffer = create_invoice(invoice_data_list)

    return send_file(pdf_buffer, as_attachment=True, download_name='invoice.pdf', mimetype='application/pdf')


@app.route('/get-invoice-data', methods=['POST'])
def get_invoice_data():
    data = request.json
    customer_data = data.get('customer_data')
    date = data.get('date', "August - 2024")
    milk_price_per_liter = data.get('milk_price_per_liter', 220)

    invoice_data_list = create_invoice_data(customer_data, date=date, milk_price_per_liter=milk_price_per_liter)

    return jsonify(invoice_data_list)



@app.get("/")
def read_root():
    return {"Hello": "Render"}

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)