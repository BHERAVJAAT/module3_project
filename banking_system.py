from abc import ABC, abstractmethod
from datetime import datetime


class InsufficientFundsError(Exception):
    """Raised when withdrawal amount is more than the allowed balance."""


class Transaction:
    """Ek single transaction ka record."""

    def __init__(self, kind, amount, balance_after):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.kind = kind
        self.amount = amount
        self.balance_after = balance_after

    def __str__(self):
        return (f"[{self.timestamp}] {self.kind:<12} "
                f"Rs.{self.amount:>10.2f} | Balance: Rs.{self.balance_after:.2f}")


class Account(ABC):
    """Abstract base class - har account type isse inherit karega."""

    _counter = 1000  # class variable for account numbers

    def __init__(self, owner, initial_deposit=0.0):
        if initial_deposit < 0:
            raise ValueError("Initial deposit negative nahi ho sakta.")
        Account._counter += 1
        self.__account_number = Account._counter   # private (encapsulation)
        self.owner = owner
        self.__balance = 0.0                        # private
        self._transactions = []
        if initial_deposit > 0:
            self.deposit(initial_deposit)

    # ---- Encapsulation: controlled access via properties ----
    @property
    def account_number(self):
        return self.__account_number

    @property
    def balance(self):
        return self.__balance

    # ---- Core methods ----
    def deposit(self, amount, kind="DEPOSIT"):
        if amount <= 0:
            raise ValueError("Deposit amount positive hona chahiye.")
        self.__balance += amount
        self._transactions.append(Transaction(kind, amount, self.__balance))
        return self.__balance

    def withdraw(self, amount, kind="WITHDRAW"):
        if amount <= 0:
            raise ValueError("Withdraw amount positive hona chahiye.")
        if not self._can_withdraw(amount):
            raise InsufficientFundsError(
                f"Insufficient funds. Available: Rs.{self.__balance:.2f}")
        self.__balance -= amount
        self._transactions.append(Transaction(kind, amount, self.__balance))
        return self.__balance

    def transfer(self, other, amount):
        """Ek account se dusre account me paise bhejna (rollback ke saath)."""
        self.withdraw(amount, kind="TRANSFER-OUT")
        try:
            other.deposit(amount, kind="TRANSFER-IN")
        except Exception:
            # Deposit fail hua to paisa wapas karo aur record hata do
            self.__balance += amount
            self._transactions.pop()
            raise

    def show_history(self):
        print(f"\n--- Transaction History: {self.owner} ({self.account_number}) ---")
        if not self._transactions:
            print("Koi transaction nahi hai.")
        for t in self._transactions:
            print(t)

    # ---- Abstraction: subclasses ko implement karna hi padega ----
    @abstractmethod
    def _can_withdraw(self, amount):
        pass

    @abstractmethod
    def account_type(self):
        pass

    def __str__(self):
        return (f"{self.account_type()} | A/C {self.account_number} | "
                f"{self.owner} | Balance: Rs.{self.balance:.2f}")


class SavingsAccount(Account):
    """Inheritance: Account se bana. Minimum balance maintain karna padta hai."""

    MIN_BALANCE = 500.0

    def __init__(self, owner, initial_deposit=MIN_BALANCE, interest_rate=0.04):
        if initial_deposit < self.MIN_BALANCE:
            raise ValueError(
                f"Savings account ke liye minimum Rs.{self.MIN_BALANCE:.2f} deposit chahiye.")
        super().__init__(owner, initial_deposit)
        self.interest_rate = interest_rate

    def _can_withdraw(self, amount):
        return self.balance - amount >= self.MIN_BALANCE

    def add_interest(self):
        interest = self.balance * self.interest_rate
        if interest > 0:
            self.deposit(interest, kind="INTEREST")
        return interest

    def account_type(self):  # Polymorphism
        return "Savings"


class CurrentAccount(Account):
    """Inheritance: Overdraft allowed."""

    def __init__(self, owner, initial_deposit=0.0, overdraft_limit=5000.0):
        super().__init__(owner, initial_deposit)
        self.overdraft_limit = overdraft_limit

    def _can_withdraw(self, amount):
        return self.balance - amount >= -self.overdraft_limit

    def account_type(self):  # Polymorphism
        return "Current"


class Bank:
    """Saare accounts manage karta hai."""

    def __init__(self, name):
        self.name = name
        self._accounts = {}

    def open_account(self, account):
        self._accounts[account.account_number] = account
        return account

    def get_account(self, number):
        if number not in self._accounts:
            raise KeyError(f"Account {number} nahi mila.")
        return self._accounts[number]

    def list_accounts(self):
        print(f"\n=== {self.name} - All Accounts ===")
        for acc in self._accounts.values():
            print(acc)  # Polymorphism: har type apna __str__ use karta hai


def main():
    bank = Bank("Python National Bank")

    alice = bank.open_account(SavingsAccount("Alice", 10000))
    bob = bank.open_account(CurrentAccount("Bob", 2000))

    alice.deposit(2500)
    alice.withdraw(1000)
    bob.withdraw(4000)            # overdraft use hoga
    alice.transfer(bob, 3000)
    print(f"Interest added: Rs.{alice.add_interest():.2f}")

    # Error handling demo
    try:
        alice.withdraw(1_000_000)
    except InsufficientFundsError as e:
        print("Error:", e)

    try:
        alice.deposit(-50)
    except ValueError as e:
        print("Error:", e)

    bank.list_accounts()
    alice.show_history()
    bob.show_history()


if __name__ == "__main__":
    main()