from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import uvicorn
from pydantic import BaseModel
import paho.mqtt.client as mqtt
import pyartnet


@dataclass
class Device:
    name: str
    ip: str
    pixels: int
    port: int = 6454


@dataclass
class Group:
    name: str
    devices: List[Device] = field(default_factory=list)


class Controller:
    def __init__(self) -> None:
        self.devices: Dict[str, Device] = {}
        self.groups: Dict[str, Group] = {}
        self.universes: Dict[str, pyartnet.ArtNetNode] = {}
        self.channels: Dict[str, pyartnet.base.Channel] = {}

    def add_device(self, name: str, ip: str, pixels: int, port: int = 6454) -> None:
        if name in self.devices:
            raise ValueError(f"Device {name} exists")
        device = Device(name=name, ip=ip, pixels=pixels, port=port)
        self.devices[name] = device
        node = pyartnet.ArtNetNode(ip, port)
        universe = node.add_universe(0)
        channel = universe.add_channel(1, pixels * 3, 'uint8')
        self.universes[name] = universe
        self.channels[name] = channel

    def add_group(self, name: str, device_names: List[str]) -> None:
        if name in self.groups:
            raise ValueError(f"Group {name} exists")
        devices = []
        for dname in device_names:
            if dname not in self.devices:
                raise ValueError(f"Device {dname} not defined")
            devices.append(self.devices[dname])
        self.groups[name] = Group(name=name, devices=devices)

    async def set_color(self, group: str, r: int, g: int, b: int) -> None:
        if group not in self.groups:
            raise ValueError(f"Group {group} not defined")
        for device in self.groups[group].devices:
            channel = self.channels.get(device.name)
            if channel is None:
                universe = self.universes[device.name]
                # DMX channel indexing starts at 1. Using 0 causes a
                # ChannelOutOfUniverseError in pyartnet.
                channel = universe.add_channel(1, device.pixels * 3, 'uint8')
                self.channels[device.name] = channel
            await channel.add_fade([r, g, b] * device.pixels, 0)


controller = Controller()
app = FastAPI()
app.mount("/ui", StaticFiles(directory="static", html=True), name="static")


class DeviceModel(BaseModel):
    name: str
    ip: str
    pixels: int
    port: int = 6454


class GroupModel(BaseModel):
    name: str
    devices: List[str]


class ColorModel(BaseModel):
    group: str
    r: int
    g: int
    b: int


@app.post('/devices')
async def create_device(device: DeviceModel):
    try:
        controller.add_device(device.name, device.ip, device.pixels, device.port)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok"}


@app.get('/devices')
def list_devices():
    return list(controller.devices.values())


@app.post('/groups')
def create_group(group: GroupModel):
    try:
        controller.add_group(group.name, group.devices)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok"}


@app.get('/groups')
def list_groups():
    return list(controller.groups.values())


@app.post('/color')
async def set_color(color: ColorModel):
    try:
        await controller.set_color(color.group, color.r, color.g, color.b)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok"}


class MQTTClient:
    def __init__(self, broker: str = 'localhost') -> None:
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        try:
            self.client.connect(broker)
        except Exception:
            # connection errors are non fatal; MQTT is optional
            pass

    def on_connect(self, client, userdata, flags, rc):
        client.subscribe("lights/color")

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode()
            parts = payload.split(',')
            group, r, g, b = parts[0], int(parts[1]), int(parts[2]), int(parts[3])
            asyncio.create_task(controller.set_color(group, r, g, b))
        except Exception:
            pass

    def loop_start(self):
        self.client.loop_start()


mqtt_client = MQTTClient()
mqtt_client.loop_start()


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
