import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import math

os.makedirs('test_images', exist_ok=True)

invoices = [
    {
        "filename": "bill_1_perfect.jpg",
        "lines": [
            "TAX INVOICE",
            "SuperMart Inc.",
            "123 Main St, Springfield",
            "Date: 15/01/2024",
            "Invoice No. INV-2024-001",
            "----------------",
            "Apples      $4.50",
            "Bread       $2.00",
            "Milk        $3.50",
            "----------------",
            "Subtotal:  $10.00",
            "GST (5%):   $0.50",
            "Total:     $10.50"
        ],
        "skew": 0,
        "noise": False
    },
    {
        "filename": "bill_2_skewed.jpg",
        "lines": [
            "RESTAURANT BILL",
            "Joe's Diner",
            "Date: 22-Feb-2024",
            "INV# 99824",
            "",
            "Burger      15.00",
            "Fries        5.00",
            "Cola         3.00",
            "Subtotal:   23.00",
            "Tax:         2.00",
            "Total: $25.00",
            "Thank you!"
        ],
        "skew": 2.5, # slight angle
        "noise": False
    },
    {
        "filename": "bill_3_noisy.jpg",
        "lines": [
            "TECH GADGETS LLC",
            "Invoice No: TECH-882",
            "Date: 05 Mar 2024",
            "",
            "Mouse        ₹1,250",
            "Keyboard     ₹2,500",
            "Total: ₹3,750"
        ],
        "skew": 0,
        "noise": True
    },
    {
        "filename": "bill_4_complex.jpg",
        "lines": [
            "ACME Corp Services",
            "Invoice No: ACME-0023",
            "Date: 12/04/2024",
            "Consulting  500.00",
            "Hosting      50.00",
            "Subtotal    550.00",
            "GST 10%      55.00",
            "TOTAL:      605.00"
        ],
        "skew": -1.5,
        "noise": False
    },
    {
        "filename": "bill_5_handwritten_like.jpg",
        "lines": [
            "Local Bakery",
            "Date: 18-04-2024",
            "Inv: 45",
            "Cake           20.00",
            "Total: $20.00"
        ],
        "skew": 0.5,
        "noise": True
    }
]

def create_receipt(data):
    # Create white canvas
    img = Image.new('RGB', (600, 800), color='white')
    d = ImageDraw.Draw(img)
    
    # default font or fallback
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except IOError:
        font = ImageFont.load_default()

    y = 50
    for line in data['lines']:
        d.text((50, y), line, fill=(0, 0, 0), font=font)
        y += 40

    # Add noise
    if data['noise']:
        # salt and pepper logic or blurring
        img = img.filter(ImageFilter.GaussianBlur(1))
        # add some specs
        noise_d = ImageDraw.Draw(img)
        for _ in range(500):
            x1 = random.randint(0, 600)
            y1 = random.randint(0, 800)
            noise_d.point((x1, y1), fill=(100, 100, 100))

    # Skew
    if data['skew'] != 0:
        # Rotate adds black background, so we make it white
        img = img.rotate(data['skew'], resample=Image.BICUBIC, fillcolor='white')

    img.save(os.path.join('test_images', data['filename']))

for bill in invoices:
    create_receipt(bill)

print("Test images generated!")
