from server import get_db_schema

print(f"Type: {type(get_db_schema)}")
print(f"Dir: {dir(get_db_schema)}")
try:
    print(f"Wrapped: {get_db_schema.__wrapped__}")
except:
    print("No __wrapped__")

try:
    print(f"Fn: {get_db_schema.fn}")
except:
    print("No fn")
