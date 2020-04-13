s/%%BALENA_MACHINE_NAME%%/raspberrypi3-64/g
s/(Dockerfile\.)[^\.]*/\1aarch64/g
s/(DKR_ARCH[=:-]+)[^$ }]+/\1aarch64/g
s/(IMG_TAG[=:-]+)[^$ }]+/\1latest/g
s/(MARIADB_HUB[=:-]+)[^$ }]+/\1lsioarmhf/g
