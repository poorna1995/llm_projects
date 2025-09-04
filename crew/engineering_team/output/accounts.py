class Account:
    def __init__(self, user_id: str, initial_deposit: float):
        """
        Initialize the account with user ID and initial deposit amount.
        
        :param user_id: Unique identifier for the user's account
        :param initial_deposit: Initial amount to fund the account
        """
        self.user_id = user_id
        self.balance = initial_deposit
        self.portfolio = {}  # Dictionary to store shares and their quantities
        self.transactions = []  # List to store transaction history

    def deposit(self, amount: float) -> None:
        """
        Deposit funds into the account.
        
        :param amount: Amount to deposit
        """
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self.balance += amount
        self.transactions.append(f"Deposited: ${amount:.2f}")

    def withdraw(self, amount: float) -> None:
        """
        Withdraw funds from the account.
        
        :param amount: Amount to withdraw
        """
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        if self.balance - amount < 0:
            raise ValueError("Insufficient funds for withdrawal.")
        self.balance -= amount
        self.transactions.append(f"Withdrew: ${amount:.2f}")

    def buy_shares(self, symbol: str, quantity: int) -> None:
        """
        Buy shares of a specified symbol.
        
        :param symbol: Stock symbol to buy
        :param quantity: Number of shares to buy
        """
        price_per_share = get_share_price(symbol)
        total_cost = price_per_share * quantity
        if total_cost > self.balance:
            raise ValueError("Insufficient funds to buy shares.")
        self.balance -= total_cost
        self.portfolio[symbol] = self.portfolio.get(symbol, 0) + quantity
        self.transactions.append(f"Bought {quantity} shares of {symbol} at ${price_per_share:.2f} each.")

    def sell_shares(self, symbol: str, quantity: int) -> None:
        """
        Sell shares of a specified symbol.
        
        :param symbol: Stock symbol to sell
        :param quantity: Number of shares to sell
        """
        if symbol not in self.portfolio or self.portfolio[symbol] < quantity:
            raise ValueError("Not enough shares to sell.")
        price_per_share = get_share_price(symbol)
        total_revenue = price_per_share * quantity
        self.balance += total_revenue
        self.portfolio[symbol] -= quantity
        if self.portfolio[symbol] == 0:
            del self.portfolio[symbol]
        self.transactions.append(f"Sold {quantity} shares of {symbol} at ${price_per_share:.2f} each.")

    def get_total_value(self) -> float:
        """
        Calculate the total value of the user's portfolio including bank balance.
        
        :return: Total value of portfolio
        """
        total_value = self.balance
        for symbol, quantity in self.portfolio.items():
            price_per_share = get_share_price(symbol)
            total_value += price_per_share * quantity
        return total_value

    def get_profit_or_loss(self) -> float:
        """
        Calculate profit or loss from the initial deposit.
        
        :return: Profit or loss amount
        """
        initial_deposit = sum(float(tx.split('$')[1]) for tx in self.transactions if "Deposited" in tx)
        return self.get_total_value() - initial_deposit

    def report_holdings(self) -> dict:
        """
        Report the current holdings of the user.
        
        :return: Dictionary of current holdings
        """
        return self.portfolio

    def report_profit_or_loss(self) -> float:
        """
        Report the current profit or loss of the user.
        
        :return: Current profit or loss
        """
        return self.get_profit_or_loss()

    def list_transactions(self) -> list:
        """
        List all transactions made by the user.
        
        :return: List of transaction strings
        """
        return self.transactions


def get_share_price(symbol: str) -> float:
    """
    Mock function to return the current price of a share based on its symbol. 
    
    :param symbol: Stock symbol
    :return: Current price of the share
    """
    prices = {
        'AAPL': 150.00,
        'TSLA': 800.00,
        'GOOGL': 2800.00,
    }
    return prices.get(symbol, 0.0)