from app.extensions import db
from datetime import datetime
from statistics import mean
from app.models.product import Inventory, Product
from app.models.sale import Sale, Sale_Item
from collections import defaultdict
import plotly.graph_objs as go
from plotly.subplots import make_subplots


# For Turnover Graph
def calculate_inventory_turnover(product):
    # Get all sales for the product
    sales = Sale_Item.query.join(Inventory).filter(Inventory.Product_id == product.id).all()
    # Calculate total quantity sold
    total_sold = sum(sale.Quantity for sale in sales)
    # Calculate average inventory
    inventories = Inventory.query.filter_by(Product_id=product.id).all()
    beginning_inventory = sum(inventory.Init_QTY for inventory in inventories)
    ending_inventory = sum(inventory.Available_QTY for inventory in inventories)
    average_inventory = mean([beginning_inventory, ending_inventory])
    
    # Calculate turnover rate
    turnover_rate = total_sold / average_inventory if average_inventory != 0 else 0
    # print(turnover_rate)
    return turnover_rate



def calculate_total_sales(product):
    # Get all sale items for the product
    sale_items = Sale_Item.query.join(Inventory).filter(Inventory.Product_id == product.id).all()
    # Calculate total quantity sold
    total_sold = sum(sale.Quantity for sale in sale_items)
    return total_sold



def calculate_average_inventory(product):
    # Get all inventory records for the product
    inventories = Inventory.query.filter_by(Product_id=product.id).all()
    # Calculate the total available quantity of the product across all inventory records
    total_available_quantity = sum(inventory.Available_QTY for inventory in inventories)
    # Calculate the average available quantity
    average_available_quantity = total_available_quantity / len(inventories) if len(inventories) != 0 else 0
    
    return average_available_quantity


def get_total_product_available_qty():
    products = Product.query.all()
    product_names = []
    total_quantities = []
    for product in products:
        # Calculate total quantity for the product
        total_quantity = sum(inventory.Available_QTY for inventory in product.Inventories)
        
        # Append product name and total quantity to the respective lists
        product_names.append(product.Name)
        total_quantities.append(total_quantity)
    return product_names,total_quantities


#Lost Cost Graphs
def show_product_lost_cost_bar():
    # Create plotly visualization for lost cost by product
    lost_cost_by_product = db.session.query(Product.Name, db.func.sum(Inventory.CostPerItem * Inventory.Lost_QTY).label('total_lost_cost')) \
        .join(Inventory)\
        .group_by(Product.id, Product.Name).all()
    

    product_names = [row[0] for row in lost_cost_by_product]
    lost_costs = [row[1] for row in lost_cost_by_product]

    lost_cost_chart = go.Figure(data=go.Bar(x=product_names, y=lost_costs))
    lost_cost_chart.update_traces(
        marker_color = ['rgb(26,118,255)','rgb(188,25,188)'],
        marker_line_width=1.5,
        opacity=0.6
    )
    return lost_cost_chart

#Proportion of products Graphs
def show_product_proportion_pie(): 
    product_names, quantities = get_total_product_available_qty()
    
    # Create a Plotly pie chart
    product_proportion_pie = go.Figure(data=[go.Pie(labels=product_names, values=quantities)])
    product_proportion_pie.update_traces(textposition='inside',hoverinfo='label+percent', textinfo='value', textfont_size=10,
            marker=dict(colors=product_names))
    product_proportion_pie.update_layout(uniformtext_minsize=20, uniformtext_mode='hide')

    return product_proportion_pie

#Sales Statistic
def show_sales_graph():
    sales = Sale.query.all()
    sales_by_date = defaultdict(float)
    # Sum sales by date
    for sale in sales:
        sales_by_date[sale.Date] += sale.Total
    # Prepare data for the graph
    dates = sorted(sales_by_date.keys())
    total_sales = [sales_by_date[date] for date in dates]
    # Create the figure and add the trace
    sales_graph = go.Figure()
    sales_graph.add_trace(go.Scatter(x=dates, y=total_sales, mode='lines', name='Total Sales'))
    # Update layout
    sales_graph.update_layout(
        xaxis=dict(type='category'), 
        yaxis_title='Sales (RM)')

    return sales_graph

# Sales, Inventory and Inventory Turnover Graphs
def show_inventory_turnover_graph():
    # turnover_rate = {product.Name: calculate_inventory_turnover(product.id) for product in products}
    products = Product.query.all()
    turnover_rate = {product.Name: calculate_inventory_turnover(product) for product in products}
    sales_data = [calculate_total_sales(product) for product in products]
    inventory_data = [calculate_average_inventory(product) for product in products]
    # print("turnover_rate: ",list(turnover_rate.values()))

    turnover_bar_figure = make_subplots(specs=[[{"secondary_y":True}]])
    turnover_bar_figure.add_trace(
        go.Bar(name="Sales",x=list(turnover_rate.keys()),y=sales_data),secondary_y=False
    )

    turnover_bar_figure.add_trace(go.Bar(name="Inventory",x=list(turnover_rate.keys()),y=inventory_data),secondary_y=False)
    turnover_bar_figure.update_traces(
        marker_color = 'rgb(26,118,255)',
        marker_line_width=1.5,
        opacity=0.6
    )
    turnover_bar_figure.update_layout(
        barmode='group', title='Sales, Inventory, and Inventory Turnover',
        xaxis=dict(title='Product'),
        plot_bgcolor="#fff"
        # yaxis=dict(title='TurnoverRate')
    )
    turnover_bar_figure.add_trace(go.Scatter(
        name="Turnover Rate",
        mode='markers+lines',
        x=list(turnover_rate.keys()),
        y = list(turnover_rate.values())),secondary_y=True)
    
    return turnover_bar_figure


# Inventory Value by Products Graph
def show_prodcut_vertical_bar():
    product_names, quantities = get_total_product_available_qty()
    vertical_product_bar = go.Figure(go.Bar(
        x = quantities,
        y = product_names,
        orientation='h'
    ))

    return vertical_product_bar