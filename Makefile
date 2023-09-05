.PHONY: openapi.json
openapi.json:
	wget -O $@ https://github.com/Bungie-net/api/raw/master/openapi.json
