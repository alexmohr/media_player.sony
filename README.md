[![Build Status](https://travis-ci.com/alexmohr/media_player.sony.svg?branch=master)](https://travis-ci.com/alexmohr/media_player.sony)
# media_player.sony

## Important!

The device needs to be in the same subnet as the Home Assistant software.
This is a limitation of the Sony Firmware, the device will not react properly to requests if the client is in a different subnet.

## Getting Started

To get started put :
* `/custom_components/sony/*` here: `<config_directory>/custom_components/sony`

When using home assistant supervised put the  contents of this repo into ````/usr/share/hassio/homeassistant/````

## Configuration

You will need to configure your device to allow the Home Assistant for remote usage. To do that, ensure that your device is turned on.
To add a device to your installation, add the Sony Legacy from integration section, then fill in the IP address or hostname of your device (it should be a static IP in your network)
Don't modify the other values and click next. After that, the device will show you a PIN and Home Assistant will allow you to re-enter that PIN.
You should be able to see the PIN code on your TV screen and type it in, then validate and that's all.

**Configuration variables**

| Key                      | Description                          |
|:-------------------------|:-------------------------------------|
| **host (Required)**      | IP Address or hostname of the device |
| **name (Required)**      | Descriptive name for the device      |
| **broadcast (Optional)** | The broadcast ip of the subnet       |
| **app_port (Optional)**  | The app port, defaults to 50202      |
| **dmr_port (Optional)**  | The dmr port, defaults to 52323      |
| **ircc_port (Optional)** | The ircc port, defaults to 50001     |

### Devices
Devices listed here configure the ports different. This list is not complete. If you devices does work with other ports please add it via a PR

| Device   | App Port | Dmr Port | Ircc  |
|:---------|:---------|:---------|:------|
| BDP-S590 | 52323    | 50202    | 52323 |

## Send commands through remote control entity
Example to trigger a command from the remote entity :
```yaml
service: remote.send_command
data:
  command: Up
target:
  entity_id: remote.sony_remote

Available commands for remote entity :
```

Here is the list of available commands, depending on your device

| Command   | Description      |
|-----------|------------------|
| Num1      | 1                |
| Num2      | 2                |
| Num3      | 3                |
| Num4      | 4                |
| Num5      | 5                |
| Num6      | 6                |
| Num7      | 7                |
| Num8      | 8                |
| Num9      | 9                |
| Num0      | 0                |
| Power     | Power            |
| Eject     | Eject            |
| Stop      | Stop             |
| Pause     | Pause            |
| Play      | Play             |
| Rewind    | Rewind           |
| Forward   | Forward          |
| PopUpMenu | Popup Menu       |
| TopMenu   | Top Menu         |
| Up        | Up               |
| Down      | Down             |
| Left      | Left             |
| Right     | Right            |
| Confirm   | Confirm          |
| Options   | Options          |
| Display   | Display          |
| Home      | Home             |
| Return    | Return           |
| Karaoke   | Karaoke          |
| Netflix   | Netflix          |
| Mode3D    | 3D mode          |
| Next      | Next chapter     |
| Prev      | Previous chapter |
| Favorites | Favorites        |
| SubTitle  | SubTitle         |
| Audio     | Audio            |
| Angle     | Angle            |
| Blue      | Blue             |
| Red       | Red              |
| Green     | Green            |
| Yellow    | Yellow           |
| Advance   | Advance          |
| Replay    | Replay           |
