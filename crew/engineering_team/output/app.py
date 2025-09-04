import gradio as gr
from accounts import Account

account = None

def create_account(user_id: str, initial_deposit: float):
    global account
    account = Account(user_id, initial_deposit)
    return f"Account created for {user_id} with an initial deposit of ${initial_deposit:.2f}"

def deposit_funds(amount: float):
    account.deposit(amount)
    return f"Deposited: ${amount:.2f}. New balance: ${account.balance:.2f}"

def withdraw_funds(amount: float):
    account.withdraw(amount)
    return f"Withdrew: ${amount:.2f}. New balance: ${account.balance:.2f}"

def buy_shares(symbol: str, quantity: int):
    account.buy_shares(symbol, quantity)
    return f"Bought {quantity} shares of {symbol}."

def sell_shares(symbol: str, quantity: int):
    account.sell_shares(symbol, quantity)
    return f"Sold {quantity} shares of {symbol}."

def get_portfolio():
    return account.report_holdings()

def get_total_value():
    return account.get_total_value()

def get_profit_or_loss():
    return account.get_profit_or_loss()

def get_transactions():
    return account.list_transactions()

with gr.Blocks() as demo:
    gr.Markdown("## Simple Account Management System for Trading Simulation")
    
    with gr.Tab("Account Setup"):
        user_id = gr.Textbox(label="User ID")
        initial_deposit = gr.Number(label="Initial Deposit", precision=2)
        create_button = gr.Button("Create Account")
        create_output = gr.Output()
        create_button.click(create_account, inputs=[user_id, initial_deposit], outputs=create_output)

    with gr.Tab("Deposit/Withdraw"):
        deposit_amount = gr.Number(label="Deposit Amount", precision=2)
        deposit_button = gr.Button("Deposit")
        deposit_output = gr.Output()
        deposit_button.click(deposit_funds, inputs=deposit_amount, outputs=deposit_output)

        withdraw_amount = gr.Number(label="Withdraw Amount", precision=2)
        withdraw_button = gr.Button("Withdraw")
        withdraw_output = gr.Output()
        withdraw_button.click(withdraw_funds, inputs=withdraw_amount, outputs=withdraw_output)

    with gr.Tab("Buy/Sell Shares"):
        buy_symbol = gr.Textbox(label="Stock Symbol (e.g., AAPL)")
        buy_quantity = gr.Number(label="Quantity")
        buy_button = gr.Button("Buy Shares")
        buy_output = gr.Output()
        buy_button.click(buy_shares, inputs=[buy_symbol, buy_quantity], outputs=buy_output)

        sell_symbol = gr.Textbox(label="Stock Symbol (e.g., AAPL)")
        sell_quantity = gr.Number(label="Quantity")
        sell_button = gr.Button("Sell Shares")
        sell_output = gr.Output()
        sell_button.click(sell_shares, inputs=[sell_symbol, sell_quantity], outputs=sell_output)

    with gr.Tab("Reports"):
        total_value_button = gr.Button("Get Total Portfolio Value")
        total_value_output = gr.Output()
        total_value_button.click(get_total_value, outputs=total_value_output)

        profit_loss_button = gr.Button("Get Profit or Loss")
        profit_loss_output = gr.Output()
        profit_loss_button.click(get_profit_or_loss, outputs=profit_loss_output)

        transactions_button = gr.Button("Get Transactions")
        transactions_output = gr.Output()
        transactions_button.click(get_transactions, outputs=transactions_output)

demo.launch()