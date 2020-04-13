s/%%BALENA_MACHINE_NAME%%/intel-nuc/g
s/(Dockerfile\.)[^\.]*/\1x86_64/g
s/(DKR_ARCH[=:-]+)[^$ }]+/\1x86_64/g
s/(IMG_TAG[=:-]+)[^$ }]+/\1intel-nuc/g
s/(MARIADB_HUB[=:-]+)[^$ }]+/\1library/g
