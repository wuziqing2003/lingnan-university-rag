import redis

r = redis.Redis(host='127.0.0.1',port=6379,db=0,decode_responses=True,protocol=2)

# r.set("demo:msg","hello redis",ex=300)

print(r.get("demo:msg"))

print(r.ttl("demo:msg"))