#!/bin/sh
# Connect IQ development helper for the Estimated_Power add-on.
# The SDK Manager and simulator run in an Ubuntu 22.04 container shown on the
# host X11 session; the compiler runs on the host with the local JDK.
#
#   ciq.sh image              build the container image (once)
#   ciq.sh sdkmanager         open the SDK Manager (sign in, download SDK + devices)
#   ciq.sh simulator          start the Connect IQ simulator
#   ciq.sh compile [device]   compile the add-on (default edge840) to the private build folder
#   ciq.sh run [device]       load the compiled add-on into the running simulator
#   ciq.sh shell              interactive shell in the container
#   ciq.sh headless           start the simulator on a virtual screen (no window on the desktop)
#   ciq.sh hl-shot OUT.png    screenshot of the virtual screen
#   ciq.sh hl-xdo ARGS...     run xdotool on the virtual screen (clicks, keys)
#   ciq.sh headless-stop      stop the virtual-screen simulator
set -eu

IMAGE=ciq-devenv:22.04
HERE=$(cd "$(dirname "$0")" && pwd)
DEV=$(dirname "$HERE")
WORKSPACE=$(dirname "$DEV")
ADDON="$WORKSPACE/Estimated_Power"
# Signing key and build output live outside the repository, in the private
# folder next to it (override with EP_PRIVATE_DIR).
PRIVATE="${EP_PRIVATE_DIR:-$(dirname "$WORKSPACE")/EstimatedPower_private}"
BUILD="$PRIVATE/build"
KEY="$PRIVATE/keys/developer_key.der"
SDK_MANAGER_DIR=${SDK_MANAGER_DIR:-$HOME/.local/opt/connectiq-sdk-manager}

run() {
    mkdir -p "$HOME/.Garmin"
    # Same absolute paths inside and outside so ~/.Garmin config stays valid on
    # the host. Host networking lets monkeydo on the host reach the simulator.
    tty_flags=""
    if [ -t 0 ]; then
        tty_flags="-it"
    fi
    # shellcheck disable=SC2086
    docker run --rm $tty_flags \
        --network host \
        --ipc host \
        -e DISPLAY="${DISPLAY:-:0}" \
        -e XAUTHORITY="$HOME/.Xauthority" \
        -e HOME="$HOME" \
        -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
        -v "$HOME/.Xauthority:$HOME/.Xauthority:ro" \
        -v "$HOME/.Garmin:$HOME/.Garmin" \
        -v "$SDK_MANAGER_DIR:$SDK_MANAGER_DIR:ro" \
        -v "$WORKSPACE:$WORKSPACE" \
        -w "$ADDON" \
        "$IMAGE" "$@"
}

current_sdk_bin() {
    cfg="$HOME/.Garmin/ConnectIQ/current-sdk.cfg"
    if [ ! -f "$cfg" ]; then
        echo "No SDK selected yet: run '$0 sdkmanager' first." >&2
        exit 1
    fi
    echo "$(sed 's:/*$::' "$cfg")/bin"
}

use_local_jdk() {
    for jdk in "$HOME"/.local/jdk/jdk-17*; do
        if [ -x "$jdk/bin/java" ]; then
            JAVA_HOME=$jdk
            PATH="$jdk/bin:$PATH"
            export JAVA_HOME PATH
            return
        fi
    done
}

HL_NAME=ciq-sim-headless
HL_DISPLAY=:99

case "${1:-}" in
    headless)
        docker rm -f "$HL_NAME" >/dev/null 2>&1 || true
        docker run -d --name "$HL_NAME" --network host --ipc host \
            -e HOME="$HOME" -e DISPLAY="$HL_DISPLAY" \
            -v "$HOME/.Garmin:$HOME/.Garmin" \
            -v "$WORKSPACE:$WORKSPACE" -w "$ADDON" \
            "$IMAGE" sh -c "Xvfb $HL_DISPLAY -screen 0 1100x1150x24 -nolisten tcp & sleep 2; exec $(current_sdk_bin)/simulator" >/dev/null
        echo "headless simulator started ($HL_NAME)"
        ;;
    hl-shot)
        docker exec "$HL_NAME" xwd -root -silent -display "$HL_DISPLAY" > "${2:?output png}.xwd"
        python3 -I "$HERE/xwd2png.py" "$2.xwd" "$2" && rm -f "$2.xwd"
        ;;
    hl-xdo)
        shift
        docker exec -e DISPLAY="$HL_DISPLAY" "$HL_NAME" xdotool "$@"
        ;;
    headless-stop)
        docker rm -f "$HL_NAME" >/dev/null 2>&1 || true
        ;;
    image)
        docker build -t "$IMAGE" \
            --build-arg UID="$(id -u)" --build-arg GID="$(id -g)" --build-arg USERNAME="$(id -un)" \
            "$HERE"
        ;;
    sdkmanager)
        run "$SDK_MANAGER_DIR/bin/sdkmanager"
        ;;
    simulator)
        run "$(current_sdk_bin)/simulator"
        ;;
    compile)
        use_local_jdk
        mkdir -p "$BUILD"
        "$(current_sdk_bin)/monkeyc" -f "$ADDON/monkey.jungle" -d "${2:-edge840}" \
            -o "$BUILD/EstimatedPower.prg" -y "$KEY" -w
        ;;
    run)
        use_local_jdk
        "$(current_sdk_bin)/monkeydo" "$BUILD/EstimatedPower.prg" "${2:-edge840}"
        ;;
    shell)
        run /bin/bash
        ;;
    *)
        sed -n '2,15p' "$0"
        exit 1
        ;;
esac
