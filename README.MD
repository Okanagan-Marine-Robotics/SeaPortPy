# SeaPort

**High-speed, reliable serial communication library for robotic submarines**

[![License: GPLv3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

---

## Features

- High-performance, low-latency serial communication
- Reliable message encoding with COBS, CRC, and MsgPack
- Pub/Sub messaging pattern
- Simple and extensible Python API

---

## Installation

Install via pip:

note that this library is not available on PyPI, so you must install it directly from the GitHub repository. Do not use `pip install seaport` as it will import the wrong package.

```bash
pip install git+https://github.com/Okanagan-Marine-Robotics/SeaPortPy
```

## Usage

The `seaport` library provides two core functions for serial communication with reliable packet framing and error checking: `subscribe` and `publish`.

### Constructor

```python
seaport(output_stream)
```

---

### Subscriber

The `Subscriber` reads and decodes incoming COBS-framed packets, verifies CRC8 checksums, unpacks MsgPack-encoded data, and dispatches messages to registered callbacks keyed by `channel_id`.

**Example:**

```python
import serial
import seaport as sp

# Example data generator: read data from a serial port

def received(data):
    print(f"Data received: {data}")

ser = serial.Serial(args.serial_port, args.baudrate, timeout=1)
seaport = sp.SeaPort(ser)

seaport.subscribe(254, lambda data: received(data))

seaport.start() # Start the subscriber to listen for incoming messages

```

### Publisher

The `Publisher` sends messages to a writeable output stream (such as a serial port). It serializes data using [MsgPack](https://msgpack.org/), adds a `channel_id`, computes a CRC-8 checksum, encodes the message using [COBS (Consistent Overhead Byte Stuffing)](https://en.wikipedia.org/wiki/Consistent_Overhead_Byte_Stuffing), and appends a null byte (`\x00`) to frame the packet.

---

- **output_stream** – A writeable binary stream, such as a serial.Serial object.

#### Method

```python
publish(channel_id: int, data: dict)
```

- **channel_id** – An integer identifier for the message channel.
- **data** – A dictionary (or any MsgPack-serializable object) to send.

#### Example:

```python
import serial
import seaport as sp

# Open serial port
ser = serial.Serial("/dev/ttyUSB0", 115200)

# Send a command on channel 1
sp.publish(1, {
    "command": "set_depth",
    "depth_meters": 10.5
})

# Clean up if needed (don't close if you still need the subscriber)
ser.close()
```

---

## Use with [ESP Bridge](https://github.com/Okanagan-Marine-Robotics/ESP32_Bridge)

The `seaport` library can be used with the [ESP Bridge](https://github.com/Okanagan-Marine-Robotics/ESP32_Bridge). If you are using this then please check the [ESP Bridge documentation](https://github.com/Okanagan-Marine-Robotics/ESP32_Bridge) for available channels and their meanings.

## Known Issues and Limitations

- The `Subscriber` currently does not handle multi-byte channel IDs; it assumes single-byte IDs (0-254).

- In the case that you receive a packet with an invalid CRC, the `Subscriber` will discard the packet without any signaling. You may want to implement your own error handling or logging.

- The `Subscriber` assumes that we receive valid COBS-encoded packets. If we send bad data, it will be stored in the `buffer` and will not be processed until valid data is received. However this will lose the current packet.
