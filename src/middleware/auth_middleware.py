def auth_middleware(func):
    def wrapper(*args, **kwargs):
        token = args[0].headers.get('Authorization')
        if not token or token != 'your_secret_token':
            return {'message': 'Unauthorized'}, 401
        return func(*args, **kwargs)
    return wrapper