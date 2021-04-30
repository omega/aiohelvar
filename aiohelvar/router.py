from aiohelvar.parser.command_type import CommandType
from aiohelvar.parser.command import Command
from .exceptions import ParserError
from .parser.parser import CommandParser
import asyncio

LINE_ENDING = b"#"

# from .config import Config
# from .groups import Groups
# from .lights import Lights
# from .scenes import Scenes
# from .sensors import Sensors
# from .errors import raise_error


class Router:
    """Control a Helvar Route."""

    def __init__(self, host, port, router_id=None):
        self.host = host
        self.port = port
        self._router_id = router_id

        self.config = None
        self.groups = None
        self.lights = None
        self.scenes = None
        self.sensors = None

        self.commands_to_send = []
        self.command_to_send = asyncio.Event()

        # self.capabilities = None
        # self.rules = None
        # self.schedules = None

    @property
    def id(self):
        """Return the ID of the router."""
        if self.config is not None:
            return self.config.routerid

        return self._router_id

    async def connect(self):
        print("Connecting...")
        reader, writer = await asyncio.open_connection(self.host, self.port)

        asyncio.create_task(self.stream_reader(reader))
        asyncio.create_task(self.stream_writer(reader, writer))

    async def stream_reader(self, reader):
        # an echo server
        print("Connected.")
        parser = CommandParser()

        while True:
            line = await reader.readuntil(LINE_ENDING)
            if line is not None:

                print(f"We've received the following: {line}")
                try:
                    command = parser.parse_command(line)
                except ParserError as e:
                    print(e)
                else:
                    print(f"Found the following command: {command}")
            await asyncio.sleep(0.1)

    async def stream_writer(self, reader, writer):

        while True:
            await self.command_to_send.wait()
            if len(self.commands_to_send) > 0:
                thing = self.commands_to_send.pop()
                print(f"found {thing} to send. Sending...")
                writer.write(thing)
                await writer.drain()
                print("Sent!")
            else:
                self.command_to_send.clear()

    async def initialize(self):

        # Attempt Connection

        await self.connect()

        await self.send_command(Command(CommandType.QUERY_ROUTER_TIME))
        await self.send_command(Command(CommandType.QUERY_GROUPS))

        # result = await self.request("get", "")

        # self.config = Config(result["config"], self.request)
        # self.groups = Groups(result["groups"], self.request)
        # self.lights = Lights(result["lights"], self.request)
        # if "scenes" in result:
        #     self.scenes = Scenes(result["scenes"], self.request)
        # if "sensors" in result:
        #     self.sensors = Sensors(result["sensors"], self.request)

    async def send_command(self, command: Command):
        await self.send_string(str(command))

    async def send_string(self, string: str):
        self.commands_to_send.append(bytes(string, 'utf-8'))
        self.command_to_send.set()
