from typing import Annotated
from pydantic import BaseModel,ValidationError,Field
import asyncio  
###定义用户注册的请求数据结构
class UserCreateSchema(BaseModel):
    username : Annotated[str,Field(min_length = 1 , max_length = 20 ,description = "用户名")]
    password : Annotated[str,Field(min_length  = 6 , max_length = 30 ,description = "密码")]

###模拟用户注册API的响应过程
async def simulate_register_api(incoming_json_data):
    print(f"\n[系统日志]收到用户注册请求: {incoming_json_data}")
   
    await asyncio.sleep(0.5)

    try:
        user = UserCreateSchema(**incoming_json_data)
        print(f"\n[系统日志]用户注册成功: {user.username}")
    except ValidationError as e:
        print(f"\n[系统日志]用户注册失败,错误原因如下！")
        print(f"错误详情: {e}")
#主函数
async def main():

    ##传入合法的数据
    good_data = {"username": "lingnan_student", "password": "perfect_password123"}
    await simulate_register_api(good_data)

    ##传入非法的数据
    bad_data = {"username": "hacker_abc", "password": "123"}
    await simulate_register_api(bad_data)

if __name__ == "__main__":
    asyncio.run(main())






