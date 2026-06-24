# main.py
# Entry point — wires together the clean service layer.

from clean_app.services import payment, notification


def run():
    charge = payment.charge("acct-123", 4200)
    note = notification.notify("acct-123", "Payment received")
    return {"charge": charge, "notification": note}


if __name__ == "__main__":
    print(run())
