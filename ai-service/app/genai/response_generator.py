
class ResponseGenerator:
    """Generate safe, consistently formatted shopping responses."""

    @staticmethod
    def _format_price(value):
        if value is None:
            return "Not available"

        try:
            price = float(value)
            return f"Rs. {price:,.2f}".rstrip("0").rstrip(".")
        except (TypeError, ValueError):
            return "Not available"

    @staticmethod
    def _format_rating(value):
        if value is None:
            return "Not available"

        try:
            return f"{float(value):.1f}"
        except (TypeError, ValueError):
            return "Not available"

    @staticmethod
    def _clean_cell(value):
        """Prevent product text from breaking Markdown table formatting."""
        if value is None or not str(value).strip():
            return "Not available"

        return " ".join(
            str(value).replace("|", "/").split()
        )

    def generate(self, user_message, intent, products):
        if not products:
            return (
                "I couldn't find any products matching your request. "
                "Try changing your category, budget, or other requirements."
            )

        lines = [
            f"Here are the products matching your search "
            f"for {self._clean_cell(user_message)}:",
            "",
            "| Product | Brand | Category | Price | Rating |",
            "|---|---|---|---:|---:|",
        ]

        for product in products:
            name = self._clean_cell(product.get("product_name"))
            brand = self._clean_cell(product.get("brand"))

            category = self._clean_cell(product.get("category"))
            subcategory = product.get("subcategory")

            if subcategory:
                subcategory = self._clean_cell(subcategory)
                if subcategory != category:
                    category = f"{category} - {subcategory}"

            price = self._format_price(product.get("price"))
            rating = self._format_rating(product.get("rating"))

            lines.append(
                f"| {name} | {brand} | {category} | {price} | {rating} |"
            )

        return "\n".join(lines)

    def generate_clarification(
        self,
        user_message,
        intent,
        taxonomy,
    ):
        candidates = taxonomy.get("candidates", [])
        options = []

        for candidate in candidates:
            category = candidate.get("category")
            subcategory = candidate.get("subcategory")

            label = category or subcategory
            if category and subcategory and category != subcategory:
                label = f"{category} - {subcategory}"

            if label and label not in options:
                options.append(label)

        if options:
            choices = "; ".join(options)
            return (
                f"Could you clarify which type you mean: {choices}?"
            )

        return (
            "Could you clarify which type of product you're looking for?"
        )
