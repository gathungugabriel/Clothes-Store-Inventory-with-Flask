from twilio.rest import Client
from flask import current_app, render_template
from weasyprint import HTML

def send_whatsapp_message(invoice_id, customer_name, total_amount):
    client = Client(current_app.config['TWILIO_ACCOUNT_SID'], current_app.config['TWILIO_AUTH_TOKEN'])

    message_body = f"New Invoice Generated:\nInvoice ID: {invoice_id}\nCustomer Name: {customer_name}\nTotal Amount: ${total_amount}"
    from_whatsapp_number = f"whatsapp:{current_app.config['TWILIO_WHATSAPP_NUMBER']}"
    to_whatsapp_number = f"whatsapp:{current_app.config['RECEIVING_WHATSAPP_NUMBER']}"

    message = client.messages.create(
        body=message_body,
        from_=from_whatsapp_number,
        to=to_whatsapp_number
    )
    return message.sid

def generate_invoice_pdf(invoice):
    rendered = render_template('invoice_template.html', invoice=invoice)
    pdf = HTML(string=rendered).write_pdf()
    return pdf
