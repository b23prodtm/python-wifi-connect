s/%%BALENA_MACHINE_NAME%%/raspberrypi3/g
s/(Dockerfile\.)[^\.]*/\1armhf/g
s/%%BALENA_ARCH%%/armhf/g
s/(DKR_ARCH[=:-]+)[^$ }]+/\1armhf/g
s/(S6_ARCH[=:-]+)[^$ }]+/\1armhf/g
s/%%S6_ARCH%%/armhf/g
s/(S6_RELEASE[=:-]+)[^$ }]+/\1v2.0.0.1/g
s/%%S6_RELEASE%%/v2.0.0.1/g
s/(IMG_TAG[=:-]+)[^$ }]+/\1latest/g
s/%%IMG_TAG%%/latest/g
s/(PRIMARY_HUB[=:-]+)[^$ }]+/\1balenalib\/raspberrypi3-ubuntu-python:3.6-bionic/g
s/%%PRIMARY_HUB%%/balenalib\/raspberrypi3-ubuntu-python:3.6-bionic/g
