
import asyncio
import random
import ssl
import json
import time
import uuid
from loguru import logger
from websockets_proxy import Proxy, proxy_connect

def read_config(file_path='config.json'):
    with open(file_path, 'r') as config_file:
        config = json.load(config_file)
    return config

def process_proxy_file(file_path):
    # 从文件读取数据
    with open(file_path, 'r') as file:
        data = [line.strip() for line in file.readlines()]

    # 处理数据并生成代理列表
    socks5_proxy_list = []

    for item in data:
        socks5_proxy_list.append(item)
        # split_item = item.split('|')
        # if len(split_item) >= 4:
            # proxy = f'socks5://{split_item[2]}:{split_item[3]}@{split_item[0]}:{split_item[1]}'
            # socks5_proxy_list.append(item)

    return socks5_proxy_list

async def connect_to_wss(socks5_proxy, user_id):
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, socks5_proxy))
    logger.info(device_id)
    while True:
        try:
            await asyncio.sleep(random.randint(1, 10) / 10)
            custom_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = "wss://proxy.wynd.network:4650/"
            server_hostname = "proxy.wynd.network"
            proxy = Proxy.from_url(socks5_proxy)
            async with proxy_connect(uri, proxy=proxy, ssl=ssl_context, server_hostname=server_hostname,
                                     extra_headers=custom_headers) as websocket:
                async def send_ping():
                    while True:
                        send_message = json.dumps(
                            {"id": str(uuid.uuid4()), "version": "4.28.2", "action": "PING", "data": {}})
                        logger.debug(send_message)
                        await websocket.send(send_message)
                        await asyncio.sleep(20)

                await asyncio.sleep(1)
                asyncio.create_task(send_ping())

                while True:
                    response = await websocket.recv()
                    message = json.loads(response)
                    logger.info(message)
                    if message.get("action") == "AUTH":
                        auth_response = {
                            "id": message["id"],
                            "origin_action": "AUTH",
                            "result": {
                                "browser_id": device_id,
                                "user_id": user_id,
                                "user_agent": custom_headers['User-Agent'],
                                "timestamp": int(time.time()),
                                "device_type": "desktop",  # Metadata desktop
                                "version": "4.28.2",  # File version sesuai data aplikasi
                                "product": "Grass",  # Nama produk sesuai informasi aplikasi
                                "copyright": "© Grass Foundation, 2024. All rights reserved."
                            }
                        }
                        logger.debug(auth_response)
                        await websocket.send(json.dumps(auth_response))

                    elif message.get("action") == "PONG":
                        pong_response = {"id": message["id"], "origin_action": "PONG"}
                        logger.debug(pong_response)
                        await websocket.send(json.dumps(pong_response))
        except Exception as e:
            logger.error(e)
            logger.error(socks5_proxy)


async def main():
    config = read_config()
    file_path = config.get('file_path', 'ip.txt')
    user_id = config.get('user_id', '')
    result = process_proxy_file(file_path)
    # 输入多组账号和相应的SOCKS5代理列表
    user_accounts = [
        {'user_id': user_id,
         'socks5_proxies': result
         }
    ]

    tasks = []
    for account in user_accounts:
        user_id = account['user_id']
        socks5_proxies = account['socks5_proxies']
        for socks5_proxy in socks5_proxies:
            task = asyncio.ensure_future(connect_to_wss(socks5_proxy, user_id))
            tasks.append(task)

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())
