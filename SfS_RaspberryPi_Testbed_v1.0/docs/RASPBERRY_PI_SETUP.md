# Three-Raspberry-Pi Setup

This guide prepares the physical testbed used by the SfS sender, receiver, and attacker programs.

## 1. Hardware

Prepare:

- three Raspberry Pi devices with 2.4 GHz Wi-Fi interfaces that support IBSS/ad-hoc mode;
- three suitable power supplies;
- three microSD cards with Raspberry Pi OS;
- temporary display/keyboard access or SSH access for initial configuration; and
- an isolated area for the wireless experiment.

To approximate the reported laboratory setup, place the devices approximately 3–5 m apart with static line of sight. Record any different placement or obstruction with the results.

## 2. Device roles and addresses

| Device | Hostname suggestion | Role | Address |
|---|---|---|---:|
| Raspberry Pi 1 | `sfs-sender` | Sender | `192.168.1.11/24` |
| Raspberry Pi 2 | `sfs-receiver` | Receiver | `192.168.1.12/24` |
| Raspberry Pi 3 | `sfs-attacker` | Attacker | `192.168.1.10/24` |

The experiment programs use UDP port `5005`.

## 3. Install Raspberry Pi OS

Install Raspberry Pi OS with Raspberry Pi Imager, boot each device, create a user account, and set a unique hostname. The official operating-system guide is:

<https://www.raspberrypi.com/documentation/computers/os.html>

Set the correct WLAN regulatory country on every device:

~~~bash
sudo raspi-config
~~~

Use **Localisation Options → WLAN Country**, then reboot if requested.

## 4. Copy the role folders

Copy only the corresponding directory to each Raspberry Pi:

| Device | Directory to copy | Suggested destination |
|---|---|---|
| Raspberry Pi 1 | `Raspberry_Pi_1_Sender/` | `~/SfS/Raspberry_Pi_1_Sender/` |
| Raspberry Pi 2 | `Raspberry_Pi_2_Receiver/` | `~/SfS/Raspberry_Pi_2_Receiver/` |
| Raspberry Pi 3 | `Raspberry_Pi_3_Attacker/` | `~/SfS/Raspberry_Pi_3_Attacker/` |

The folders can be copied using a USB drive, SCP over a temporary managed network, or another controlled transfer method.

Example from a workstation, replacing `<user>` as required:

~~~bash
scp -r Raspberry_Pi_1_Sender <user>@192.168.1.11:~/SfS/
scp -r Raspberry_Pi_2_Receiver <user>@192.168.1.12:~/SfS/
scp -r Raspberry_Pi_3_Attacker <user>@192.168.1.10:~/SfS/
~~~

## 5. Install system packages

Run on all three devices:

~~~bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv chrony iw wireless-tools
~~~

Raspberry Pi OS releases use NetworkManager for normal network configuration. Official network configuration documentation is available at:

<https://www.raspberrypi.com/documentation/computers/configuration.html>

## 6. Install Python dependencies

The following execution commands assume that the required Python packages have already been installed. A virtual environment may be used for dependency isolation, but it is not required by the SfS programs.

### Raspberry Pi 1

~~~bash
cd ~/SfS/Raspberry_Pi_1_Sender
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
~~~

### Raspberry Pi 2

~~~bash
cd ~/SfS/Raspberry_Pi_2_Receiver
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
~~~

### Raspberry Pi 3

~~~bash
cd ~/SfS/Raspberry_Pi_3_Attacker
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
~~~

## 7. Confirm IBSS support

On every device:

~~~bash
iw list
~~~

Under **Supported interface modes**, confirm that `IBSS` is listed. The Wi-Fi adapter and driver must support IBSS mode.

## 8. Create the 2.4 GHz IBSS network

The following NetworkManager method is recommended on current Raspberry Pi OS releases.

Run once on every device:

~~~bash
sudo nmcli radio wifi on
sudo nmcli connection add type wifi ifname wlan0 con-name sfs-ibss ssid SFS-TESTBED
sudo nmcli connection modify sfs-ibss 802-11-wireless.mode adhoc
sudo nmcli connection modify sfs-ibss 802-11-wireless.band bg
sudo nmcli connection modify sfs-ibss 802-11-wireless.channel 6
sudo nmcli connection modify sfs-ibss ipv4.method manual
sudo nmcli connection modify sfs-ibss ipv4.never-default yes
sudo nmcli connection modify sfs-ibss ipv6.method disabled
~~~

Assign the device-specific address.

On Raspberry Pi 1:

~~~bash
sudo nmcli connection modify sfs-ibss ipv4.addresses 192.168.1.11/24
sudo nmcli connection up sfs-ibss
~~~

On Raspberry Pi 2:

~~~bash
sudo nmcli connection modify sfs-ibss ipv4.addresses 192.168.1.12/24
sudo nmcli connection up sfs-ibss
~~~

On Raspberry Pi 3:

~~~bash
sudo nmcli connection modify sfs-ibss ipv4.addresses 192.168.1.10/24
sudo nmcli connection up sfs-ibss
~~~

If the connection already exists, do not add it again; modify and activate the existing `sfs-ibss` connection.

Check each device:

~~~bash
ip -4 address show wlan0
iwconfig wlan0
~~~

The interface should show the assigned address, the `SFS-TESTBED` ESSID, ad-hoc/IBSS mode, and channel 6.

### Manual fallback for older images

Use this only when NetworkManager is not managing `wlan0`. Replace `<DEVICE_IP>` with the address assigned above:

~~~bash
sudo ip link set wlan0 down
sudo iwconfig wlan0 mode ad-hoc
sudo iwconfig wlan0 essid SFS-TESTBED
sudo iwconfig wlan0 channel 6
sudo ip addr flush dev wlan0
sudo ip addr add <DEVICE_IP>/24 dev wlan0
sudo ip link set wlan0 up
~~~

Do not mix the NetworkManager and manual methods on the same run.

## 9. Test connectivity

From Raspberry Pi 1:

~~~bash
ping -c 4 192.168.1.12
ping -c 4 192.168.1.10
~~~

From Raspberry Pi 3:

~~~bash
ping -c 4 192.168.1.12
~~~

Resolve packet loss or incorrect addressing before starting the Python programs.

## 10. Synchronize the clocks with Chrony

Clock synchronization is mandatory because sender and receiver independently derive time-based sequences.

If all three devices can reach the same trusted NTP sources, keep Chrony enabled and verify synchronization:

~~~bash
sudo systemctl enable --now chrony
chronyc sources -v
chronyc tracking
~~~

For an isolated IBSS run, Raspberry Pi 1 can provide the local Chrony reference to Raspberry Pis 2 and 3.

### Raspberry Pi 1

Edit:

~~~bash
sudo nano /etc/chrony/chrony.conf
~~~

Ensure that the configuration contains:

~~~text
allow 192.168.1.0/24
local stratum 8
makestep 0.1 3
~~~

Then:

~~~bash
sudo systemctl restart chrony
~~~

### Raspberry Pis 2 and 3

Edit `/etc/chrony/chrony.conf`, add the server line below, and ensure that the file contains one active `makestep` directive:

~~~text
server 192.168.1.11 iburst prefer
makestep 0.1 3
~~~

Then:

~~~bash
sudo systemctl restart chrony
sudo chronyc -a makestep
chronyc sources -v
chronyc tracking
~~~

On Raspberry Pis 2 and 3, verify that `192.168.1.11` is the selected source. Do not begin data collection while a device reports that it is unsynchronized.

Chrony command documentation is available at:

<https://chrony-project.org/doc/4.0/chronyc.html>

## 11. Configure the attacker receive buffer

The ordinary attacker sleeps before returning to receive the next queued datagram. Before a high-volume ordinary-replay run, execute on Raspberry Pi 3:

~~~bash
sudo sysctl -w net.core.rmem_max=52428800
sudo sysctl -w net.core.rmem_default=52428800
sysctl net.core.rmem_max
sysctl net.core.rmem_default
~~~

These commands apply until the next reboot.

## 12. Calibrate a different physical setup

The supplied receiver uses a 0.29 s mean delay measured from 1,000 synchronized packets in the authors' laboratory setup.

When the hardware, network, software, or placement changes materially:

1. synchronize the devices;
2. run the receiver without an attacker;
3. send 1,000 packets;
4. stop the receiver so that it writes `receiver_results.xlsx`; and
5. calculate the mean of the `Travel Time (s)` column.

For example:

~~~bash
python3 - <<'PY'
import pandas as pd

data = pd.read_excel("receiver_results.xlsx")
print(data["Travel Time (s)"].mean())
PY
~~~

Pass the newly measured value to either receiver with `--mean-delay-s`; do not
edit the source file. Retain the default 0.29 s when reproducing the supplied
testbed configuration.

## 13. Final pre-run checklist

- All three devices show the expected static IP address.
- Raspberry Pi 1 can ping Raspberry Pis 2 and 3.
- Raspberry Pi 3 can ping Raspberry Pi 2.
- Chrony reports synchronized clocks.
- The same UDP port is configured everywhere.
- Only one attacker process is running.
- The intended THV and replay delay are recorded.
- Previous Excel output files have been moved or renamed.
- The experiment is running on a controlled network.
