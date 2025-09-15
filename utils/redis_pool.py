# utils/redis_pool.py
import redis

pool = redis.ConnectionPool(
    host="192.168.64.8",
    port=6379,
    #password="huangxuanyao11",
    decode_responses=True,
)
r = redis.Redis(connection_pool=pool)

def save_code(phone, code, expire=60):
    r.set("sms_{}".format(phone), code, ex=expire)

def get_code(phone):
    return r.get("sms_{}".format(phone))

def del_code(phone):
    r.delete("sms_{}".format(phone))

def too_often(phone, seconds=60):
    """ 发送频率限制：若60秒内发过，则返回 True """
    key = "sms_flag_{}".format(phone)
    if r.get(key):
        return True
    r.set(key, 1, ex=seconds)
    return False
