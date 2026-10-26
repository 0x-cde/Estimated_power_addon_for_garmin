# Runtime for Garmin's Connect IQ SDK Manager and simulator.
# Both are built against WebKitGTK 4.0 / libjpeg8, which Debian 13 (LMDE 7)
# no longer ships; Ubuntu 22.04 still does. The compiler (monkeyc) is plain
# Java and runs on the host, so this image is only for the GUI tools.
FROM ubuntu:22.04

ARG UID=1000
ARG GID=1000
ARG USERNAME=developer

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        libwebkit2gtk-4.0-37 \
        libjpeg-turbo8 \
        libcurl4 \
        libusb-1.0-0 \
        libsecret-1-0 \
        libsm6 \
        libxxf86vm1 \
        libcanberra-gtk3-module \
        dbus-x11 \
        fonts-dejavu-core \
        openjdk-17-jre-headless \
        xdotool \
        xvfb \
        x11-apps \
        x11-utils \
    && rm -rf /var/lib/apt/lists/*

# Same user/uid as on the host so files written to ~/.Garmin stay owned by you
# and the absolute paths the SDK Manager records also work on the host.
RUN groupadd -g ${GID} ${USERNAME} && useradd -m -u ${UID} -g ${GID} -s /bin/bash ${USERNAME}
USER ${USERNAME}
