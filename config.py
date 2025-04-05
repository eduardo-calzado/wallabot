# Wallabot Configuration File
"""
This configuration file controls the behavior of the Wallabot script.
Edit these settings to customize how the bot works.
"""

#######################
# Email Notifications #
#######################

# The email address that will send notifications
username = ''

# Email password (for Gmail, use an app-specific password: https://myaccount.google.com/apppasswords)
password = ''

# The email address that will receive notifications
receiver = ''

########################
# Search Configuration #
########################

# The Wallapop search URL with all search parameters
# Parameters explained:
# - min_sale_price: Minimum price in euros
# - max_sale_price: Maximum price in euros
# - keywords: Search terms (URL encoded)
# - filters_source: Source of filters (usually default_filters)
# - longitude/latitude: Location coordinates for local search
OFFERS_URL ='https://es.wallapop.com/app/search?min_sale_price=500&max_sale_price=600&keywords=Playstation%205%20pro&filters_source=default_filters&longitude=-3.69196&latitude=40.41956'

######################
# Logging Behavior   #
######################

# Enable detailed logging for debugging (slows down execution slightly)
DEBUG = False

# Write logs to file (wallabot.log)
ENABLE_FILE_LOGGING = True

######################
# Filtering Options  #
######################

# Maximum number of items to check per search (limits processing time)
MAX_ITEMS_TO_CHECK = 30

# Skip processing reserved items completely 
SKIP_RESERVED_ITEMS = True

# Only process items with shipping available
SHIPPING_REQUIRED = True

# Minimum seller rate required (skip items with fewer ratings)
SKIP_WITH_LESS_THAN_SELLER_RATE = 3

# Minimum seller rating count required (skip items with fewer ratings)
SKIP_WITH_LESS_THAN_RATING_COUNTER = 5

# Minimum number of sales required (skip items with fewer sales)
SKIP_WITH_LESS_THAN_SALES_NUMBER = 3

# Skip items from professional sellers
SKIP_PROFESIONAL_SELLER = False
