"""Entry point — imports services which reach production (P12)."""

from test_app.services import billing

def main():
    """Main entry point."""
    result = billing.process_payment(99.99, "token_xyz")
    print(result)

if __name__ == "__main__":
    main()
