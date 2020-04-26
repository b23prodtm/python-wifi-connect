s/%%BALENA_MACHINE_NAME%%/raspberrypi3/g
s/(Dockerfile\.)[^\.]*/\1armhf/g
s/(DKR_ARCH[=:-]+)[^$ }]+/\1armhf/g
s/(IMG_TAG[=:-]+)[^$ }]+/\1latest/g
s/(PRIMARY_HUB[=:-]+)[^$ }]+/\1betothreeprod\/raspberrypi3-php/g
