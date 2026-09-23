# Fixposition Setp:

## Web Interface:

1. Connect your pc with Fixposition wifi with SSID starting with **fp-**. The password for the Wifi will be **1234567890**.
2. Open a webrowser and to wepage **10.0.1.1** to access the dashboard for fixposition.

## Software upgrade:

To update the software version of the Vision-RTK 2, head to the "System → Update" panel in the web interface and either click into the marked area and select the SWU file or drag and drop the corresponding SWU file inside the marked area


## Configuration:

On the top of the page, you should be able to see the configuration tab from which you can configure the Fixposition according to your requirements.

### Fusion Configuration: 

In this section, the following configuration options are available:

• **Autostart**: Once enabled, the Fusion engine will be launched automatically on system bootup. 
(Note: Enabling this will not start the Fusion engine directly.)

• **Housing**: Prototype (i.e., 3D-printed) or Standard (i.e., aluminum).

• **Tuning mode**: Expected platform dynamics (in our case its **Slow robot**).

• **GNSS extrinsics**: Position of the GNSS antennas with respect to the Vision-RTK 2 sensor frame in meters. These values should be accurate to the mm level.

### GNSS Configuration:

You can use your own correction data configuration here to receive your desired correction data.

### Network Configuration:

In this configuration tab, you can configure the network of the fixposition such as 

• ***Wi-Fi client***: Wi-Fi network you want the fixposition to connect to as it requires Wi-Fi at the start of fusion for localization.

• ***Wi-Fi access point***: Can change the SSID and password of the Wifi network of fixposition.

• ***Eathernet***. Change the IP to your desired access over ethernet to your pc.

### I/O Configuration:

Select the **TCP0** option in all the sections in **Output messages** table except the ones that start to highlight in orange color on selection if TCP0 box.

## Status:

Once you have updated and configured the Fixpositin, then you can start the fusion by pressing **start** button. Once started, the two main options to pay attention are **IMU Status** as ***converging*** and **Baseline Status** as ***green***.
