from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive
import os
import time

http = HTTP()
tables = Tables()
pdf = PDF()
archive = Archive()

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    browser.configure(
        slowmo=100,
    )
    open_robot_order_website()
    close_annoying_modal()
    orders = get_orders()
    
    for order in orders:
        process_order(order)
    
    archive_receipts()

def open_robot_order_website():
    browser.goto("https://robotsparebinindustries.com/#/robot-order")

def get_orders():
    """
    Downloads the orders CSV file, reads it into a table, and returns the orders.
    """
    csv_url = "https://robotsparebinindustries.com/orders.csv"
    csv_path = "./orders.csv"
    http.download(csv_url, csv_path, overwrite=True)
    orders_table = tables.read_table_from_csv(csv_path)
    return orders_table.to_list()

def process_order(order):
    """
    This function will take a single order and handle the processing.
    """
    order_number = order['Order number']
    print(f"Processing order {order_number}:")
    
    fill_the_form(order)
    preview_robot()
    submit_order(order_number)
    order_another_robot()
    close_annoying_modal()
    
    content = f"""
    <html>
    <body>
    <h1>Order Number: {order_number}</h1>
    <p>Robot Configuration:</p>
    <ul>
        <li>Head: {order['Head']}</li>
        <li>Body: {order['Body']}</li>
        <li>Legs: {order['Legs']}</li>
    </ul>
    <p>Shipping Address: {order['Address']}</p>
    </body>
    </html>
    """
    
    pdf_file = store_receipt_as_pdf(order_number, content)
    screenshot = screenshot_robot(order_number)
    embed_screenshot_to_receipt(screenshot, pdf_file)

def store_receipt_as_pdf(order_number, content):
    output_dir = "./output/receipts"
    os.makedirs(output_dir, exist_ok=True) 
    receipt_filename = os.path.join(output_dir, f"receipt_{order_number}.pdf")
    pdf.html_to_pdf(content, receipt_filename)
    return receipt_filename

def screenshot_robot(order_number):
    output_dir = "./output/screenshots"
    os.makedirs(output_dir, exist_ok=True)
    screenshot_filename = os.path.join(output_dir, f"robot_{order_number}.png")
    
    page = browser.page()
    page.screenshot(path=screenshot_filename)
    return screenshot_filename

def embed_screenshot_to_receipt(screenshot, pdf_file):
    output_pdf = f"output/modified_{os.path.basename(pdf_file)}"
    pdf.add_watermark_image_to_pdf(
        image_path=screenshot,
        source_path=pdf_file,
        output_path=output_pdf
    )
    print(f"Screenshot embedded into {output_pdf}")

def close_annoying_modal():
    page = browser.page()
    page.click("button.btn-dark")
    print("Closed the annoying modal")

def archive_receipts():
    receipts_dir = "./output/receipts"
    zip_file_path = "./output/receipts_archive.zip"
    
    archive.archive_folder_with_zip(receipts_dir, zip_file_path)
    print(f"Receipts have been archived to {zip_file_path}")

def fill_the_form(order):
    page = browser.page()
    
    page.select_option("select#head", str(order['Head']))
    page.check(f'input[type="radio"][value="{order["Body"]}"]')
    
    legs_element = page.locator('input[type="number"][name^="1729"]')
    legs_element.fill(str(order['Legs']))

    page.fill('input#address', order['Address'])

def preview_robot():
    page = browser.page()
    page.click("button#preview")

def submit_order(order_number):
    page = browser.page()
    
    while True:
        page.click("button#order")
        
        error_alerts = page.locator("div.alert.alert-danger")
        
        if error_alerts.count() == 0:
            print("Order submitted successfully.")
            break
        
        print("Submit failed due to an alert. Re-clicking the order button to close the alert...")
        time.sleep(1) 

    screenshot_path = f"output/receipts/receipt_{order_number}.png"
    page.screenshot(path=screenshot_path)
    print(f"Screenshot taken: {screenshot_path}")

    order_another_button = page.locator("button#order-another")
    order_another_button.wait_for(state="visible", timeout=30000)
    print("Order another button is now visible.")

def order_another_robot():
    page = browser.page()
    button = page.locator("button#order-another")

    max_retries = 5
    for attempt in range(max_retries):
        try:
            button.wait_for(state="visible", timeout=30000)
            button.click()
            print("Clicked on 'Order another robot' button.")
            break 
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(1) 
    else:
        print("Failed to click 'order-another' button after several attempts.")
