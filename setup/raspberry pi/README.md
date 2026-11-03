# Setting up the project on the Raspberry Pi

1. Flash an SD-Card with Raspbian Lite (use the official Raspberry Pi Imager), setting up WiFi credentials (if using WiFi) and enabling SSH.
2. Disable analog audio output: `sudo nano /boot/firmware/config.txt` and change `dtparam=audio=on` to `dtparam=audio=off`. This is because the NeoPixel library uses the Pi's PWM capabilities which are also used for audio.
3. Install SWIG and linux build tools:

    ```bash
    sudo apt update && sudo apt install swig build-essential python3-dev -y
    ```

4. Install the liblgpio driver:

    ```bash
    sudo apt install liblgpio-dev -y
    ```

5. Install the package manager `uv`:

    ```bash
        curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

6. Clone this repo onto the Pi (using `git clone`, you might need to install git first)
7. Run `uv sync --no-dev` in the project root folder to install the dependencies
8. To run the app, use `sudo /home/<user>/.local/bin/uv run --no-dev weasley_clock`. Sudo is necessary because the NeoPixel library uses Direct Memory Access which can only be used with elevated privileges.

_Note that the python app will be terminated with the terminal session. The Raspberry Pi will keep the session alive for about 2 hours which should be enough for testing. For more permanent sessions, tools like `tmux` or `systemd` services are recommended (see below)._

## Calibration

To find out which LEDs correspond to which semantic location, you can also run `sudo /home/<user>/.local/bin/uv run --no-dev calibrate_clock`. This prints out each location's name and lights up the corresponding LEDs. This can be useful to determine where on the clock face to glue the different locations' icons (if you decide to print the icons separately from the clock face).

## Setting Up the System for Production

For deployment/a user test, it is helpful to setup a `systemd` service so that the python script automatically restarts after the Pi boots, eliminating the need to create a new ssh session after somebody accidentally unplugs the device, for example. The setup process is straightforward:

1. Create a new file using `nano`, for example: `sudo nano /etc/systemd/system/weasley_clock.service`
2. Use the following template as a starting point and add your concrete `WorkingDirectory` and `ExecStart` paths:

    ```ini
    [Unit]
    Description=Weasley Clock Service
    # ensure the Pi's clock has synced
    After=network-online.target time-sync.target
    Wants=network-online.target time-sync.target

    [Service]
    # systemd services run as root by default, so 'sudo' is not needed

    WorkingDirectory=/home/<user>/weasley-clock

    ExecStart=/home/<user>/.local/bin/uv run --no-dev weasley_clock

    # Automatically restart the script if it crashes
    Restart=always
    RestartSec=10

    # Ensure Python output is sent straight to syslog without buffering
    Environment=PYTHONUNBUFFERED=1

    [Install]
    WantedBy=multi-user.target
    ```

3. Let `systemd` load this configuration:

    ```bash
    sudo systemctl daemon-reload
    ```

4. Configure the service to automatically start on boot:

    ```bash
    sudo systemctl enable weasley_clock.service
    ```

5. Start the service right now:

    ```bash
    sudo systemctl start weasley_clock.service
    ```

Now you can check the status of the service via

```bash
sudo systemctl status weasley_clock.service
```

. You can also view the most recent console output/logs this way.

To allow `sytemd` to enforce a NTP clock synchronization, ensure the service necessary is active:

```bash
sudo systemctl enable systemd-time-wait-sync.service
sudo systemctl daemon-reload
# restart the weasley clock service to apply changes (if systemd-time-wait-sync) was not already active
sudo systemctl restart weasley_clock.service
```

To disable the `weasley_clock.service`, use

```bash
sudo systemctl stop weasley_clock.service
sudo systemctl disable weasley_clock.service
```

To reduce the risk of memory corruption in the event of sudden power loss (e.g., if somebody removes the wall adapter connected to the Pi), you can enable the "overlay file system" via `sudo raspi-config`. This makes the Pi mount the SD card as read-only and "overlay" another file system in RAM. This also means that any changes will not survive a reboot and logs will be lost.
