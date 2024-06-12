# utils.py

# Define category and subcategory prefixes
prefixes = {
    'shirt': {'casual': 'SC', 'official': 'SO'},
    'trouser': {'casual': 'TC', 'official': 'TO'},
    'tshirt': {'casual': 'TSC', 'official': 'TSO'},
    'sweater': {'casual': 'SWC', 'official': 'SWO'},
    'coat': {'casual': 'CC', 'official': 'CO'},
    'suit': {'casual': 'SUC', 'official': 'SUO'},
    'tie': 'TIE',
    'belt': 'BLT',
    'short': 'SHRT',
    'shoes': {'casual': 'SHC', 'official': 'SHO'},
    'boxers': 'BX',
    'vest': 'VST'
}

# Function to generate the tag
def generate_tag(category, subcategory=None, item_code=1):
    """
    Generates a unique tag for a product based on its category and subcategory.

    Args:
        category (str): The category of the product (e.g., 'shirt', 'tie').
        subcategory (str, optional): The subcategory of the product (e.g., 'casual', 'official'). Default is None.
        item_code (int): The unique code for the item within its category and subcategory. Default is 1.

    Returns:
        str: The generated product tag.

    Raises:
        ValueError: If the category or subcategory is invalid.
    """
    if category in prefixes:
        if isinstance(prefixes[category], dict):
            if subcategory and subcategory in prefixes[category]:
                return f"{prefixes[category][subcategory]}{item_code:04d}"
            else:
                raise ValueError(f"Invalid subcategory for {category}")
        else:
            return f"{prefixes[category]}{item_code:04d}"
    else:
        raise ValueError("Invalid category")
