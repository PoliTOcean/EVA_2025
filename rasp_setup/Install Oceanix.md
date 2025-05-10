To install Oceanix:

1.  Clone the Oceanix repository:
    ```bash
    git clone https://github.com/PoliTOcean/Oceanix.git
    cd Oceanix
    ```

2.  Source the install script:
    ```bash
    source install.sh
    ```

3. To use I2C, enable it:

   *   Open the Raspberry Pi configuration:
        ```bash
        sudo raspi-config
        ```
   *   Navigate to `Interface Options` -> `I2C` -> `<Yes>` to enable it.
   *   Reboot the Raspberry Pi for the changes to take effect:
        ```bash
        sudo reboot
        ```

4.  Automatic Execution with Systemd

To automatically start Oceanix as a service on boot, you can use systemd.

*   Create the `oceanix.service` file in `/etc/systemd/system/`:

    ```bash
    sudo nano /etc/systemd/system/oceanix.service
    ```

*   Add the following content to the `oceanix.service` file:

    ```
    [Unit]
    Description=Oceanix Service
    After=network.target

    [Service]
    ExecStart=/usr/bin/chrt -f 99 /home/politocean/firmware/Oceanix/build/Oceanix
    WorkingDirectory=/home/politocean/firmware/Oceanix/build
    Restart=always
    User=root
    Environment=DISPLAY=:0
    CPUSchedulingPolicy=fifo
    CPUSchedulingPriority=99

    [Install]
    WantedBy=multi-user.target
    ```

*   **Important:** Verify that the `ExecStart` and `WorkingDirectory` paths are correct for your Oceanix installation.  The `User` should be the user that owns the Oceanix installation.

*   Enable the Oceanix service:

    ```bash
    sudo systemctl enable oceanix.service
    ```

*   restart the Oceanix service:

    ```bash
    sudo systemctl restart oceanix.service
    ```

*   Start the Oceanix service:

    ```bash
    sudo systemctl start oceanix.service
    ```

*   Check the status of the Oceanix service:

    ```bash
    sudo systemctl status oceanix.service
    ```

*   To stop the Oceanix service:

    ```bash
    sudo systemctl stop oceanix.service
    ```

*   To disable the Oceanix service:

    ```bash
    sudo systemctl disable oceanix.service
    ```