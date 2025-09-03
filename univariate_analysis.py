import csv
import math
import os
import re
from collections import Counter

# Source data file
DATA_FILE = 'df_tratado.csv'
OUTPUT_DIR = 'outputs'
CAT_DIR = os.path.join(OUTPUT_DIR, 'categorical')
NUM_DIR = os.path.join(OUTPUT_DIR, 'numeric')

os.makedirs(CAT_DIR, exist_ok=True)
os.makedirs(NUM_DIR, exist_ok=True)

# Load data into list of dictionaries
with open(DATA_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Helper functions for numeric cleaning
perc_re = re.compile(r'([0-9\.]+)')
price_re = re.compile(r'[\$,]')

def parse_percentage(value):
    match = perc_re.search(value or '')
    return float(match.group(1)) if match else None

def parse_price(value):
    if not value:
        return None
    return float(price_re.sub('', value))

def parse_bathrooms_text(value):
    match = perc_re.search(value or '')
    return float(match.group(1)) if match else None

def parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def save_ascii_bar(pairs, path):
    if not pairs:
        return
    max_count = max(count for _, count in pairs)
    with open(path, 'w', encoding='utf-8') as f:
        for label, count in pairs:
            bar_len = int((count / max_count) * 50) if max_count else 0
            if count > 0 and bar_len == 0:
                bar_len = 1
            bar = '#' * bar_len
            f.write(f"{label}: {bar} ({count})\n")

# Categorical variables for univariate analysis
categorical_vars = [
    'property_type',
    'property_type.1',
    'room_type',
    'host_is_superhost',
    'host_identity_verified',
    'neighbourhood_cleansed',
    'host_response_time',
    'instant_bookable',
    'has_availability',
    'host_location'
]

summary_tables = {}
for col in categorical_vars:
    counter = Counter(row.get(col, '') or 'NA' for row in rows)
    summary_tables[col] = counter
    pairs = counter.most_common()
    with open(os.path.join(CAT_DIR, f'{col}_freq.csv'), 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['category', 'count'])
        writer.writerows(pairs)
    save_ascii_bar(pairs, os.path.join(CAT_DIR, f'{col}_freq.txt'))

# Numeric variables to categorize using Sturges rule
numeric_vars = {
    'host_response_rate': parse_percentage,
    'host_acceptance_rate': parse_percentage,
    'host_total_listings_count': parse_float,
    'accommodates': parse_float,
    'bathrooms_text': parse_bathrooms_text,
    'beds': parse_float,
    'price': parse_price,
    'maximum_nights_avg_ntm': parse_float,
    'availability_365': parse_float,
    'number_of_reviews': parse_float,
    'review_scores_value': parse_float,
    'reviews_per_month': parse_float
}

num_tables = {}
for col, parser in numeric_vars.items():
    values = [parser(row.get(col, '')) for row in rows]
    values = [v for v in values if v is not None]
    if not values:
        continue
    n = len(values)
    k = math.ceil(math.log2(n) + 1)
    min_v, max_v = min(values), max(values)
    width = (max_v - min_v) / k if k else 1
    bins = [min_v + i * width for i in range(k+1)]
    counts = [0] * k
    for v in values:
        idx = min(int((v - min_v) / width), k - 1)
        counts[idx] += 1
    categories = [f"[{bins[i]:.2f}, {bins[i+1]:.2f})" for i in range(k)]
    pairs = list(zip(categories, counts))
    num_tables[col] = pairs
    with open(os.path.join(NUM_DIR, f'{col}_sturges_freq.csv'), 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['range', 'count'])
        writer.writerows(pairs)
    save_ascii_bar(pairs, os.path.join(NUM_DIR, f'{col}_sturges_freq.txt'))

# Display summary tables
print('Resumenes de variables categóricas:')
for col, counter in summary_tables.items():
    print(f"\n{col}")
    for category, count in counter.most_common(5):
        print(f"{category}: {count}")

print('\nCategorías de variables numéricas (Sturges):')
for col, table in num_tables.items():
    print(f"\n{col}")
    for rng, count in table[:5]:
        print(f"{rng}: {count}")
