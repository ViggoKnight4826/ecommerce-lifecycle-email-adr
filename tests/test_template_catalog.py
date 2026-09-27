from template_catalog import LifecycleKind, build_template_definition


def test_receipt_subject_matches_order_lifecycle_copy() -> None:
    definition = build_template_definition(
        LifecycleKind.receipt,
        store_name="Northwind Goods",
        namespace="dev-shop",
    )

    assert definition.name == "dev-shop-receipt"
    assert definition.subject == "Your receipt for order #{{order_number}}"
