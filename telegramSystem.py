import html
import os
import markdown
from bs4 import BeautifulSoup
from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import date
from app.extensions import db
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.product import Inventory, Product
 
user_state = ""
 
print("Bot Start...")
API_KEY: Final = '7038381879:AAFW53rnahyEubeiBuB_t63-xYcKivWcIoI'
BOT_USERNAME: Final = '@UOW_S_Mart_bot'

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir,'app.db')
db = SQLAlchemy(app)
# Create the engine and sessionmaker for SQLAlchemy
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
Session = sessionmaker(bind=engine)
 
# /info
async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    content = str(read_md('info.md'))
    await update.message.reply_text(text = content)
 
 
# /announce
async def announce_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # content = read_announcement_md('announcement.md')
    
    content = str(read_md('announcement.md'))
    await update.message.reply_text(text = content)
 
 
# /pricetdy
async def pricetdy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
     # Create a session
    session = Session()

    # Query products within the session
    products_in_stock = (
        session.query(Product)
        .filter(Product.Status == "InStock")
        .join(Inventory, Product.id == Inventory.Product_id)
        .filter(Inventory.ExpiryDate >= date.today())  # Expiry date should be today or later
        .filter(Inventory.Available_QTY > 0)  # Available quantity should be greater than 0
        .order_by(Inventory.StockInDate)  # Order by stock in date to get the first inventory
        .all()
    )
    content = ''' Today Price \n'''
    if products_in_stock:
        i = 1
        
        for product_in_stock in products_in_stock:
            first_inventory = product_in_stock.Inventories[0]  # Assuming you want the first inventory
            content += f"{i}. {product_in_stock.Name}  -   RM {first_inventory.RetailPrice:.2f} \n"
            i+=1
    else:
        print("No products meet the criteria.")
    
    # Close the session after use
    session.close()
    # content = str(read_md('price_today.md'))
    await update.message.reply_text(text = content)
 
 
# /promo
async def promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    content = str(read_md('promo.md'))
    await update.message.reply_text(text = content)
 
 
# /FAQ
async def faq_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    content = str(read_md('faq.md'))
    await update.message.reply_text(text = content)


def read_md(filename):
    basedir = os.path.abspath(os.path.dirname(__file__))
    file_path = os.path.join(basedir, "telegram_md", filename)
    with open(file_path , 'r', encoding='utf-8') as f:
        md_content = f.read()
        # Convert Markdown to HTML and then extract text
        html_content = markdown.markdown(md_content)
        content = BeautifulSoup(html_content, 'html.parser')
        return content.get_text()

 
async def error(update: Update, context:ContextTypes.DEFAULT_TYPE):
    print(f'Update{update} caused error {context.error}')
 
if __name__ == "__main__":
 
    print("Bot Run")
    app = Application.builder().token(API_KEY).build()
 
    # Commands
    app.add_handler(CommandHandler('info',info_command))
    app.add_handler(CommandHandler('announce',announce_command))
    app.add_handler(CommandHandler('pricetdy',pricetdy_command))
    app.add_handler(CommandHandler('promo',promo_command))
    app.add_handler(CommandHandler('faq',faq_command))

 
    # Message
    app.add_error_handler(error)
    # print("Bot Polling...")
    app.run_polling(poll_interval=0.5)