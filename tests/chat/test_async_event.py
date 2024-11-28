import asyncio

async def waiter(event):
    print('Waiter: 开始监听...')
    while True:
        if await event.wait():  # 当event.set()被调用时返回True
            print('Waiter: 收到事件，退出循环!')
            break  # 退出循环
        print('Waiter: 继续等待...')

async def trigger(event):
    print('Trigger: 等待3秒后触发事件')
    await asyncio.sleep(3)
    event.set()
    print('Trigger: 事件已触发')

async def main():
    event = asyncio.Event()
    
    # 创建并运行任务
    await asyncio.gather(
        waiter(event),
        trigger(event)
    )

asyncio.run(main())