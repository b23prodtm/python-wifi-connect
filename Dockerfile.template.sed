s/%%BALENA_MACHINE_NAME%%/intel-nuc/g
s/(Dockerfile\.)[^\.]*/\1x86_64/g
s/(DKR_ARCH[=:-]+)[^$ }]+/\1x86_64/g
s/(IMG_TAG[=:-]+)[^$ }]+/\1latest/g
