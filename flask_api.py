from flask import Flask, jsonify, request, send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import calendar
import os

app = Flask(__name__)


def parse_milk_data(milk_data):
    parsed_data = []
    for part in milk_data.strip('()').split(')('):
        quantity, days = map(float, part.split('-'))
        parsed_data.extend([quantity] * int(days))
    return parsed_data


def create_invoice_data(customer_data, company_name="Yousaf Meo", date="August - 2024", milk_price_per_liter=220):
    invoice_list = []
    # Extract month and year from the date
    month_name, year = date.split(' - ')
    month_number = list(calendar.month_name).index(month_name)

    # Calculate the number of days in the given month
    num_days = calendar.monthrange(int(year), month_number)[1]

    for data in customer_data:
        name, milk_data, previous_balance = data.split(':')
        parsed_milk_quantities = parse_milk_data(milk_data)

        day_milk_map = {day + 1: qty for day, qty in enumerate(parsed_milk_quantities)}
        total_milk = sum(parsed_milk_quantities)
        total_price = total_milk * milk_price_per_liter

        previous_balance = float(previous_balance)
        total_amount = total_price + previous_balance

        invoice_data = {
            "company_name": company_name,
            "client_name": name,
            "day_milk_map": day_milk_map,
            "total_price": round(total_price, 2),
            "total_amount": round(total_amount, 2),
            "total_milk": f"{total_milk:.2f}(L)",
            "date": date,
            "previous_balance": round(previous_balance, 2),
            "num_days": num_days  # Pass number of days in the month
        }

        invoice_list.append(invoice_data)

    return invoice_list


def create_invoice(invoice_data_list, filename, milk_price_per_liter):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # Set up grid dimensions for the 3x3 matrix
    rows = 2
    cols = 3
    invoice_width = width / cols
    invoice_height = height / rows

    customer_summaries = []
    grand_total = 0

    for i, invoice_data in enumerate(invoice_data_list):
        col = i % cols
        row = (i // cols) % rows
        if i != 0 and i % (rows * cols) == 0:
            c.showPage()

        x_position = col * invoice_width + 20
        y_position = height - (row + 1) * invoice_height + invoice_height - 20

        company_name = invoice_data['company_name']
        client_name = invoice_data['client_name']
        day_milk_map = invoice_data['day_milk_map']
        total_amount = invoice_data['total_amount']
        total_price = invoice_data['total_price']
        previous_balance = invoice_data['previous_balance']
        total_milk = invoice_data['total_milk']
        date = invoice_data['date']
        num_days = invoice_data['num_days']  # Get number of days in the month

        c.setFont("Helvetica-Bold", 10)
        c.drawString(x_position, y_position, f"{client_name}")

        c.setFont("Helvetica", 7)
        c.drawString(x_position, y_position - 12, f"{company_name} / {date}")

        y_position -= 30
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x_position, y_position, "Day")
        c.drawString(x_position + 50, y_position, "Milk (L)")
        c.drawString(x_position + 100, y_position, "Price (Rs)")

        c.line(x_position, y_position - 2, x_position + 150, y_position - 2)

        y_position -= 10
        c.setFont("Helvetica", 7)
        for day in range(1, num_days + 1):  # Dynamically use the correct number of days
            milk_qty = day_milk_map.get(day, 0)
            price = milk_qty * milk_price_per_liter

            c.drawString(x_position, y_position, str(day))
            c.drawString(x_position + 50, y_position, f"{milk_qty:.2f}")
            c.drawString(x_position + 100, y_position, f"{int(price)}")

            y_position -= 10

            c.line(x_position + 40, y_position + 30, x_position + 40, y_position + 7)
            c.line(x_position + 90, y_position + 30, x_position + 90, y_position + 7)

        c.line(x_position, y_position + 8, x_position + 150, y_position + 8)

        c.setFont("Helvetica", 9)
        c.drawString(x_position, y_position - 5, "Total Milk")
        c.drawString(x_position + 50, y_position - 5, total_milk)
        c.drawString(x_position + 100, y_position - 5, f"{int(total_price)}")

        y_position -= 20
        c.drawString(x_position, y_position + 5, "Previous Balance")
        c.drawString(x_position + 100, y_position + 5, f"{int(previous_balance)}")

        y_position -= 20
        c.line(x_position, y_position + 20, x_position + 150, y_position + 20)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x_position, y_position + 5, "Total Balance")
        c.drawString(x_position + 100, y_position + 5, f"{int(total_amount)}")

        customer_summaries.append((client_name, total_amount))
        grand_total += total_amount

    c.showPage()
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, height - 50, "Customer Summary")
    col_count = 0

    y_summary_position = height - 80
    c.setFont("Helvetica", 10)
    for client_name, total_amount in customer_summaries:
        if y_summary_position < 30:
            col_count += 1
            y_summary_position = height - 80
            x_position = (col_count * (width / 2)) + 30
        else:
            x_position = 30 + (col_count * (width / 2))

        c.drawString(x_position, y_summary_position, f"{client_name}: Rs.{int(total_amount)}")
        y_summary_position -= 20

    c.setFont("Helvetica-Bold", 12)
    c.drawString(30 + (col_count * (width / 2)), y_summary_position - 100, f"Grand Total: Rs.{int(grand_total)}")

    c.save()


# Example route to get JSON invoice data
@app.route('/api/invoice_data', methods=['POST'])
def get_invoice_data():
    request_data = request.json
    customer_data = request_data.get('customer_data', [])
    company_name = request_data.get('company_name', "Yousaf Meo")
    date = request_data.get('date', "August - 2024")
    milk_price_per_liter = request_data.get('milk_price_per_liter', 220)

    invoice_data_list = create_invoice_data(customer_data, company_name, date, milk_price_per_liter)
    return jsonify(invoice_data_list)


# Example route to generate and download PDF invoice
@app.route('/api/invoice_pdf', methods=['POST'])
def generate_invoice_pdf():
    request_data = request.json
    customer_data = request_data.get('customer_data', [])
    company_name = request_data.get('company_name', "Yousaf Meo")
    date = request_data.get('date', "August - 2024")
    milk_price_per_liter = request_data.get('milk_price_per_liter', 220)

    if not customer_data:
        return jsonify({"error": "Customer data is required"}), 400

    invoice_data_list = create_invoice_data(customer_data, company_name, date, milk_price_per_liter)
    filename = "Customer_invoice.pdf"
    create_invoice(invoice_data_list, filename, milk_price_per_liter)

    return send_file(filename, as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='10000', debug=True)
