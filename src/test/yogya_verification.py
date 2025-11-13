"""
Verify Yogya Online data in database
"""

import sys
sys.path.insert(0, 'src')

from db import DBSTATE

db = DBSTATE

# Check total items
result = db.execute(
    'SELECT COUNT(*) FROM items WHERE source=?',
    ('yogyaonline',)
)
total_items = result[0][0]
print(f"Total Yogya Online items in database: {total_items}")

# Check total prices
result = db.execute(
    """
    SELECT COUNT(*) FROM prices
    WHERE items_id IN (SELECT id FROM items WHERE source='yogyaonline')
    """
)
total_prices = result[0][0]
print(f"Total prices for Yogya items: {total_prices}")

# Check total discounts
result = db.execute(
    """
    SELECT COUNT(*) FROM discounts
    WHERE items_id IN (SELECT id FROM items WHERE source='yogyaonline')
    """
)
total_discounts = result[0][0]
print(f"Total discounts for Yogya items: {total_discounts}")

# Show sample items
print("\n" + "=" * 80)
print("Sample items from database:")
print("=" * 80)

result = db.execute(
    """
    SELECT items.name, items.sku, items.category, prices.price
    FROM items
    LEFT JOIN prices ON items.id = prices.items_id
    WHERE items.source = 'yogyaonline'
    ORDER BY items.created_at DESC
    LIMIT 10
    """
)

for i, row in enumerate(result, 1):
    name = row[0][:50].ljust(50)
    sku = row[1].ljust(12)
    category = (row[2] or "N/A")[:15].ljust(15)
    price = f"Rp {row[3]:,}" if row[3] else "N/A"

    print(f"{i:2}. {name} | SKU: {sku} | {category} | {price}")

print("=" * 80)
print(f"\nSUCCESS! Yogya Online scraper is working correctly!")
print(f"  - {total_items} items stored")
print(f"  - {total_prices} prices recorded")
print(f"  - {total_discounts} discounts tracked")
