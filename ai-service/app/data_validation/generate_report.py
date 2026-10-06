import pandas as pd

from app.data_validation.dietary_validator import DietaryValidator


INPUT_PATH = "/app/data/phase1/master_products.csv"
REPORT_PATH = "/validation/dietary_validation_report.csv"


def main():

    print("Loading dataset...")

    df = pd.read_csv(INPUT_PATH)

    print(f"Products loaded: {len(df)}")

    report = DietaryValidator.validate(df)

    report.to_csv(
        REPORT_PATH,
        index=False
    )

    print(f"Issues found: {len(report)}")
    print(f"Report saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()