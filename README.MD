# SeaPort

**High-speed, reliable serial communication library for robotic submarines**

[![License: GPLv3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

---

## Features

- High-performance, low-latency serial communication
- Reliable message encoding with COBS, CRC, and MsgPack
- Pub/Sub messaging pattern with `Subscriber` and `Publisher` classes
- Simple and extensible Python API

---

## Installation

Install via pip:

note that this library is not available on PyPI, so you must install it directly from the GitHub repository. Do not use `pip install seaport` as it will import the wrong package.

```bash
pip install git+https://github.com/Okanagan-Marine-Robotics/SeaPortPy
```

## Usage

The `seaport` library provides two core classes for serial communication with reliable packet framing and error checking: `Subscriber` and `Publisher`.

---

### Subscriber

The `Subscriber` reads and decodes incoming COBS-framed packets, verifies CRC8 checksums, unpacks MsgPack-encoded data, and dispatches messages to registered callbacks keyed by `channel_id`.

**Example:**

```python
import serial
from seaport import Subscriber

# Example data generator: read data from a serial port
def serial_data_gen(port="/dev/ttyUSB0", baudrate=115200):
    ser = serial.Serial(port, baudrate, timeout=1)
    try:
        while True:
            if ser.in_waiting:
                yield ser.read(ser.in_waiting)
    finally:
        ser.close()

# Create subscriber with data source generator
sub = Subscriber(serial_data_gen())

# Define callback for channel ID 1
def on_channel_1(msg):
    print("Received on channel 1:", msg)

# Register callback
sub.subscribe(1, on_channel_1)

# Start feeding data and dispatching callbacks
while True:
    sub.feed()

```

### Publisher

The `Publisher` class sends messages to a writeable output stream (such as a serial port). It serializes data using [MsgPack](https://msgpack.org/), adds a `channel_id`, computes a CRC-8 checksum, encodes the message using [COBS (Consistent Overhead Byte Stuffing)](https://en.wikipedia.org/wiki/Consistent_Overhead_Byte_Stuffing), and appends a null byte (`\x00`) to frame the packet.

---

#### Constructor

```python
Publisher(output_stream)
```

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
from seaport import Publisher

# Open serial port
ser = serial.Serial("/dev/ttyUSB0", 115200)

# Create Publisher
pub = Publisher(ser)

# Send a command on channel 1
pub.publish(1, {
    "command": "set_depth",
    "depth_meters": 10.5
})

# Clean up
ser.close()
```

## Known Issues and Limitations

- The `Subscriber` currently does not handle multi-byte channel IDs; it assumes single-byte IDs (0-254).

- In the case that you receive a packet with an invalid CRC, the `Subscriber` will discard the packet without any signaling. You may want to implement your own error handling or logging.

- The `Subscriber` assumes that we receive valid COBS-encoded packets. If we send bad data, it will be stored in the `buffer` and will not be processed until valid data is received.
