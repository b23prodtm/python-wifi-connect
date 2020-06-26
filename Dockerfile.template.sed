s/%%BALENA_MACHINE_NAME%%/intel-nuc/g
s/(Dockerfile\.)[^\.]*/\1x86_64/g
s/%%BALENA_ARCH%%/x86_64/g
s/(DKR_ARCH[=:-]+)[^$ }]+/\1x86_64/g
s/(S6_ARCH[=:-]+)[^$ }]+/\1amd64/g
s/%%S6_ARCH%%/amd64/g
s/(S6_RELEASE[=:-]+)[^$ }]+/\1v2.0.0.1/g
s/%%S6_RELEASE%%/v2.0.0.1/g
s/(IMG_TAG[=:-]+)[^$ }]+/\1latest/g
s/%%IMG_TAG%%/latest/g
s/(PRIMARY_HUB[=:-]+)[^$ }]+/\1balenalib\/intel-nuc-ubuntu-node:bionic-build/g
s/%%PRIMARY_HUB%%/balenalib\/intel-nuc-ubuntu-node:bionic-build/g
