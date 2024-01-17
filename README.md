# Gaze Control - Assistive Technology Based on Gaze-Interaction
Gaze Control allows you to control a computer and communicate with your surroundings using nothing but your eyes. It is powered by the [Neon](https://pupil-labs.com/products/neon) which provides the needed eye tracking functionality.

The current version of Gaze Control is a work in progress and it is still a bit rough around the edges. Nonetheless, it is already usable and we are looking for your feedback to improve it further.

Currently, you can only run Gaze Control from source, so a bit of technical knowledge is required.

# Requirements & Installation

## Neon Eye Tracker
To use Gaze Control you need a [**Neon**](https://pupil-labs.com/products/neon) eye tracker. The Neon Companion app needs to be installed and running on the Neon Companion device.

The Neon Companion device and the computer running Gaze Control need to be in the **same local network**, so they can communicate with each other.

Gaze Control is primarily developed and tested for **Windows 11**, but it also works on Windows 10 and MacOS. There are currently known issues when running on Linux.

**Python 3.10+** is required.

To be successful with Gaze Control, you need to use it with a sufficiently **large monitor**. We recommend ~24-26 inches.

Issues may occur when using the app with 2 monitors. If you have 2 monitors and run into problems, please disable one of them before using Gaze Control.

## Dependencies
First, clone this repository:
```bash
git clone git@github.com:pupil-labs/gaze-control.git
```

To run the software you need to install the following dependencies:
```bash
cd gaze-control/
pip install -r requirements.txt
```

### Ubuntu
If you are running this on Ubuntu you also need to install the following:
```bash
sudo apt install libxcb-cursor0
```

### MacOS
The first time you run this project, MacOS may prompt you to grant permission for the app to utilize the accessibility features of the operating system. If you do not see this message or fail to grant permission, mouse control functionality will not work.
To manually grant permission

- Open your System Settings and navigate to Privacy & Security
- Within that section go to Accessibility
- Find the terminal app you're using and allow control.


# Usage
Execute the following command to start the application:
```bash
python src/main.py
```

## Configuring Gaze Control
**Connecting to Neon:** When starting the Gaze Control app, the settings window will open up first allowing you to connect to your Neon device. When `Auto Discover` is enabled, the app will attempt to find your Neon device in the local network automatically. 

If automatic discovery fails, you can disable it and enter the IP address and port of the Neon device manually. You can find those values in the Neon Companion app when you select `Stream` on the home screen. Note, that they are reported as `<IP>:<Port>`, e.g. `192.168.178.28:8080`.

Once you are connected to your Neon device, the main window as well as a debugging video showing the live feed of the data captured by Neon will open up. This feed includes gaze estimation results and thus shows where the wearer of Neon is looking in their field of view.

**Marker Detection:** Gaze Control uses markers in the corners of the screen to track the screen. Successful detection of those markers in the video feed is critical for the app to work properly.

First, make sure that the screen is centered in the video feed and that all the markers are visible. ~~If a marker is successfully detected it will be shown with a green border, otherwise with a red border.~~ If the markers are not detected well, try to adjust the `Marker Brightness` in the settings to improve their contrast in the video feed.

If the video feed is generally too dark or too bright, hurting the marker detection, you can also try adapting the exposure settings of Neon. Specifically, open the settings in the Neon Companion app and decrease the `Backlight compensation` value to make the video feed darker or increase it to make it brighter.

Once the markers are detected well, you are ready to start using the app! You should see a circular indicator on the screen indicating where on the screen you are looking.

## Using Gaze Control
Gaze Control allows you to select things on the screen by "dwelling" on them with your eyes. After a pre-defined amount of dwell time, which can be configured in the settings, a selection will be triggered at the location.

The progress of the dwell is visualized by the growing green circle inside the gaze indicator. When a selection is performed, you will hear a click sound. 

What happens when you select something depends on the current mode of the app though. On startup you are in "Viewing Mode", which does not perform any actions when you select something.

To change the mode, you need to open the mode menu. You can do that by looking slightly beyond the left edge of your monitor (i.e. do no longer look onto the screen but look past the left edge of the screen). You can then select the mode you want to use by dwelling on it.

## Clicking Mode
While in "CLicking Mode", you can click anywhere on the screen by dwelling on it. A mouse click will be triggered at the location you are dwelling on.

This allows you to operate the computer as if you were using a mouse. You can open applications, click on buttons, etc.

## Zoom Mode
Sometimes it can be difficult to click on something because it is too small. In "Zoom Mode" you can zoom in on a specific area of the screen to make it easier to click on things.

Simply look at the area you want to zoom in on and dwell on it. The area will then be zoomed in and you can click on things inside of it.

## Keyboard Mode
The keyboard can be toggled using the "KEYS" button in the bottom right. In this mode a keyboard is shown on the screen that allows you to type text using your eyes.

Selecting one of the keys will trigger the corresponding key press in the currently active application underneath Gaze Control.

While the keyboard is enabled, selecting things outside of the Gaze Control app is disabled. This means if you want to type inside of e.g. a text editor, you need to open the text editor first, position the cursor at the right location, and then enable the keyboard mode.

# Calibration
If the gaze estimation results on the screen are insufficient in accuracy, you have the option to perform a calibration. To start a calibration, switch to calibration mode in the settings.


A series of gaze targets will then be presented on the screen. Your task is to look at them continuously one after the other.

Try not to blink while the target is green. It is fine to blink while a target is still red, so you can blink briefly between all targets.

Once all targets have been presented, the calibration result will be output in the terminal and applied to the gaze targets immediately. The calibration will be saved in the `predictor.pkl` file. To rest the calibration, you can either delete this file and restart the application, or execute the calibration procedure again.

When you start Gaze Control, it will automatically use the calibration file if one is available.