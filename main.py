from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def parse_milk_data(milk_data):
    parsed_data = []
    for part in milk_data.strip('()').split(')('):
        quantity, days = map(float, part.split('-'))
        parsed_data.extend([quantity] * int(days))
    return parsed_data


def create_invoice_data(customer_data, company_name="Yousaf Meo", date="August - 2024", milk_price_per_liter=220):
    invoice_list = []

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
            "milk_data": milk_data,
            "previous_balance": round(previous_balance, 2)
        }

        invoice_list.append(invoice_data)

    return invoice_list


def create_invoice(invoice_data_list, filename):
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
        milk_data = invoice_data['milk_data']
        date = invoice_data['date']

        c.setFont("Helvetica-Bold", 10)
        c.drawString(x_position, y_position, f"{client_name.upper()}")

        # c.setFont("Helvetica", 8)
        # c.drawString(x_position, y_position - 12, company_name)

        c.setFont("Helvetica", 7)
        c.drawString(x_position, y_position - 12, f"{company_name} / {date}")

        y_position -= 30
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x_position, y_position, "Day")
        c.drawString(x_position + 50, y_position, "Milk (L)")
        c.drawString(x_position + 100, y_position, "Price (Rs)")

        # Draw the horizontal line under the headers
        c.line(x_position, y_position - 2, x_position + 150, y_position - 2)

        y_position -= 10
        c.setFont("Helvetica", 7)
        for day in range(1, 32):  # August has 31 days
            milk_qty = day_milk_map.get(day, 0)
            price = milk_qty * 220

            # Draw the values
            c.drawString(x_position, y_position, str(day))
            c.drawString(x_position + 50, y_position, f"{milk_qty:.2f}")
            c.drawString(x_position + 100, y_position, f"{int(price)}")

            y_position -= 10

            # Draw vertical lines in the table
            c.line(x_position + 40, y_position + 30, x_position + 40, y_position + 7)
            c.line(x_position + 90, y_position + 30, x_position + 90, y_position + 7)

        # Draw the final horizontal line after the last row
        c.line(x_position, y_position + 8, x_position + 150, y_position + 8)

        c.setFont("Helvetica", 9)
        # Summary of totals at the bottom
        c.drawString(x_position, y_position - 5, "Total Milk")
        c.drawString(x_position + 50, y_position - 5, total_milk)
        c.drawString(x_position + 100, y_position - 5, f"{int(total_price)}")

        y_position -= 20
        c.drawString(x_position, y_position + 5 , "Previous Balance")
        c.drawString(x_position + 100, y_position + 5 , f"{int(previous_balance)}")

        y_position -= 20
        c.line(x_position, y_position + 20, x_position + 150, y_position + 20)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x_position, y_position + 5, "Total Balance")
        c.drawString(x_position + 100, y_position + 5, f"{int(total_amount)}")

        customer_summaries.append((client_name, total_amount, milk_data))
        grand_total += total_amount

    c.showPage()
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, height - 50, date)
    col_count = 0

    y_summary_position = height - 80
    c.setFont("Helvetica", 10)
    for client_name, total_amount, milk_data in customer_summaries:
        if y_summary_position < 30:  # Start a new column if near the bottom
            col_count += 1
            y_summary_position = height - 80
            x_position = (col_count * (width / 2)) + 30
        else:
            x_position = 30 + (col_count * (width / 2))

        c.drawString(x_position, y_summary_position, f"{client_name}: {milk_data} : {int(total_amount)}")
        y_summary_position -= 20

    c.setFont("Helvetica-Bold", 12)
    c.drawString(30 + (col_count * (width / 2)), y_summary_position - 100, f"Grand Total: Rs.{int(grand_total)}")

    c.save()

# Example customer data
customer = [
    "Gaffer:(5-7)(4-22)(0-1)(2-1):000",
    "Noman:(4-31):00",
    "Anwar garden:(1.5-31):00",
    "Israr:(1.5-31):00",
    "Master Rustum:(3.25-31):00",
    "Waheed:(0.5-31):00",
    "Sajaad:(0.5-31):00",
    "Asif 1:(0.75-31):00",
    "khatak 1:(0.5-31):00",
    "khatak 2:(0.5-31):00",
    "Asif Police:(0.455-31):00",
    "Rana k Braber:(1.75-31):800",
    "Saqib:(2-17):9200",
    "Tanveer:(1.5-31):00",
    "Azeem:(0.5-31):6245",
    "Ishaq:(0.5-31):12710",
    "naser:(0.5-31):00",
    "Anwaar:(1.5-31):14590",
    "Perchun:(1.5-31):00",
    "Magbol:(1.5-31):3185",
    "Arshad:(1-16):33375",
    "Ateeq:(05-23):11115",
    "Ayyaz:(1-31):8230",
    "Saleem:(0.5-23):16000",
    "fazan:(1-31):00",
    "Iqbal:(0.455-31):000",
    "Ajmal:(0.5-28):00",
    "Gohar:(1-31):000",
    "Imvan:(0.75-31):5115",
    "Waqas:(1-31):000",
    "Anwar Usman:(1.25-31):000",
    "Shahid:(1-31):3280",
    "Adil:(1-31):000",
    "Ayaan:(0.77-31):000",
    "Jamal:(1-31):000",
    "Rashid:(1.5-31):000",
    "Umar:(1-31):000",
    "Raja Suleman 01:(2.5-31):000",
    "Nihaal:(0.5-31):000",
    "Akhter E:(1-31):000",
    "Rang ke Samney:(0.363-31):600",
    "Babo:(0.5-31):000",
    "Rana:(1-31):00",
    "Rahat:(0.5-31):0",
    "Zafar:(0.5-31):000",
    "Basit:(0.5-31):000",
    "Junaid:(0.36-31):000",
    "Imran 01:(0.134-31):000",
    "Imran 02:(0.77-31):000",
    "Sameer:(0.77-31):000",
    "Shairaz:(0.77-31):000",
    "Ashraf foji:(1-31):000",
    "Afzal:(0.455-31):000",
    "Mango:(0.455-31):000"
]


# Generate the invoice data
invoice_data_list = create_invoice_data(customer)

# Create the invoice PDF with multiple invoices and a summary page
create_invoice(invoice_data_list, "multiple_invoices_with_summary.pdf")

