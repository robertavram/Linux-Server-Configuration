db_container = "localhost"
app_files = ""
item_categories = [
    'Style',
    'Beauty',
    "Travel",
    "Shopping",
    'Winter',
    'Summer',
    'Fall',
    'Spring',
    'Casual',
    'Work',
    "Night-Out",
    "Sports"]


DB_connection = "postgresql://catalog:funnymonkeys@{}:5432/catalog".format(db_container)
