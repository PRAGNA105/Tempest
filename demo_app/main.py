# main.py
# Entry point — deliberately CLEAN itself (no prod URLs, no prod imports).
# It only wires together the service layer.

from demo_app.services import payment, notification


def run():
    charge = payment.charge("acct-123", 4200)
    note = notification.notify("acct-123", "Payment received")
    return {"charge": charge, "notification": note}


if __name__ == "__main__":
    print(run())
