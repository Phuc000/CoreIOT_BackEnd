def format_json_response(data, status_code=200):
    return {
        "status": status_code,
        "data": data
    }

def log_request(request):
    print(f"Request received: {request.method} {request.path} with body: {request.json}")

def validate_json(schema, json_data):
    from jsonschema import validate, ValidationError
    try:
        validate(instance=json_data, schema=schema)
        return True
    except ValidationError as e:
        print(f"JSON validation error: {e.message}")
        return False