from slowapi import Limiter
from slowapi.util import get_remote_address

# Создаем лимитер
limiter = Limiter(key_func=get_remote_address) 